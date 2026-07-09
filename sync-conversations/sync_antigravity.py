#!/usr/bin/env python3
"""
Antigravity 2.0 Conversation Sync & Normalization Utility
=========================================================
Este script sincroniza de forma bidirecional as conversas do Antigravity 2.0.

Modos:
  --push: Exporta as conversas locais para a pasta de backup, substituindo os IDs
          e caminhos locais por placeholders (ex: {{WORKSPACE_URI}}).
  --pull: Importa as conversas da pasta de backup para a pasta local do Antigravity,
          substituindo os placeholders pelos metadados específicos do PC local.
"""

import os
import sys
import sqlite3
import shutil
import json
import argparse
import urllib.parse
import re

# --- Helper de Varint Protobuf ---
def decode_varint(data, pos):
    result, shift = 0, 0
    while pos < len(data):
        b = data[pos]
        result |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            return result, pos + 1
        shift += 7
        pos += 1
    return result, pos

def encode_varint(value):
    result = b''
    while value > 0x7F:
        result += bytes([(value & 0x7F) | 0x80])
        value >>= 7
    result += bytes([value & 0x7F])
    return result or b'\x00'

# --- Parser/Serializer Genérico de Protobuf ---
def parse_protobuf(data):
    fields = []
    pos = 0
    while pos < len(data):
        tag, pos = decode_varint(data, pos)
        wire = tag & 7
        field_num = tag >> 3
        if wire == 2:
            length, pos = decode_varint(data, pos)
            val = data[pos:pos+length]
            pos += length
            try:
                nested = parse_protobuf(val)
                if serialize_protobuf(nested) == val:
                    fields.append((field_num, wire, nested))
                else:
                    fields.append((field_num, wire, val))
            except Exception:
                fields.append((field_num, wire, val))
        elif wire == 0:
            val, pos = decode_varint(data, pos)
            fields.append((field_num, wire, val))
        elif wire == 1:
            val = data[pos:pos+8]
            pos += 8
            fields.append((field_num, wire, val))
        elif wire == 5:
            val = data[pos:pos+4]
            pos += 4
            fields.append((field_num, wire, val))
        else:
            raise ValueError(f"Wire type não suportado: {wire}")
    return fields

def serialize_protobuf(fields):
    res = b''
    for field_num, wire, val in fields:
        tag = (field_num << 3) | wire
        res += encode_varint(tag)
        if wire == 2:
            if isinstance(val, list):
                inner_bytes = serialize_protobuf(val)
            else:
                inner_bytes = val
            res += encode_varint(len(inner_bytes))
            res += inner_bytes
        elif wire == 0:
            res += encode_varint(val)
        elif wire == 1 or wire == 5:
            res += val
    return res

def modify_fields(fields, translations):
    modified = []
    for field_num, wire, val in fields:
        if wire == 2:
            if isinstance(val, list):
                val = modify_fields(val, translations)
            elif isinstance(val, bytes):
                try:
                    s = val.decode('utf-8')
                    modified_str = s
                    for old_val, new_val in translations.items():
                        if old_val in s:
                            modified_str = modified_str.replace(old_val, new_val)
                    val = modified_str.encode('utf-8')
                except Exception:
                    pass
        modified.append((field_num, wire, val))
    return modified

# --- Funções de Detecção Automática ---
def get_local_antigravity_paths():
    home = os.path.expanduser("~")
    gemini_dir = os.path.join(home, ".gemini", "antigravity")
    config_dir = os.path.join(home, ".gemini", "config")
    return gemini_dir, config_dir

def check_git_remote(path):
    config_path = os.path.join(path, ".git", "config")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            remotes = re.findall(r"url\s*=\s*(.*)", content)
            for r in remotes:
                if "obsidian-personal-vault" in r.lower():
                    return True
        except Exception:
            pass
    return False

def find_obsidian_project(config_dir):
    projects_dir = os.path.join(config_dir, "projects")
    if not os.path.isdir(projects_dir):
        return None
        
    for filename in os.listdir(projects_dir):
        if filename.endswith(".json"):
            path = os.path.join(projects_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                resources = data.get("projectResources", {}).get("resources", [])
                if resources:
                    uri = resources[0].get("gitFolder", {}).get("folderUri", "")
                    local_path = urllib.parse.unquote(uri.replace("file:///", ""))
                    # Tratamento Windows drive letter
                    if len(local_path) >= 3 and local_path[1] == ':' and local_path[0] == '/':
                        local_path = local_path[1:]
                    
                    # 1. Tenta identificar via Git Remote
                    if check_git_remote(local_path) or check_git_remote(os.path.dirname(local_path)):
                        return {
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "uri": uri,
                            "path": local_path
                        }
                    # 2. Fallback por nome na URI
                    if "obsidian-personal-vault" in uri.lower():
                        return {
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "uri": uri,
                            "path": local_path
                        }
            except Exception:
                pass
    return None

def extract_workspace_id_from_local_dbs(gemini_dir):
    convs_dir = os.path.join(gemini_dir, "conversations")
    if not os.path.isdir(convs_dir):
        return None
        
    try:
        files = [f for f in os.listdir(convs_dir) if f.endswith(".db") and not f.endswith(("-shm", "-wal"))]
        files.sort(key=lambda f: os.path.getmtime(os.path.join(convs_dir, f)), reverse=True)
    except Exception:
        files = os.listdir(convs_dir)
        
    for filename in files:
        if filename.endswith(".db") and not filename.endswith(("-shm", "-wal")):
            db_path = os.path.join(convs_dir, filename)
            try:
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT data FROM trajectory_metadata_blob WHERE id='main'")
                row = cur.fetchone()
                conn.close()
                if row and row[0]:
                    parsed = parse_protobuf(row[0])
                    # O Workspace ID fica no Outer Field 3 do protobuf
                    for fnum, wire, val in parsed:
                        if fnum == 3 and isinstance(val, bytes):
                            ws_id = val.decode('utf-8')
                            if len(ws_id) == 36 and '-' in ws_id:
                                return ws_id
            except Exception:
                pass
    return None
def normalize_uri(uri):
    unquoted = urllib.parse.unquote(uri).lower().replace('\\', '/')
    if unquoted.endswith('/'):
        unquoted = unquoted[:-1]
    if unquoted.startswith('file:///'):
        unquoted = unquoted[8:]
    elif unquoted.startswith('file:'):
        unquoted = unquoted[5:]
    return unquoted

def find_workspace_id_fallback(config_dir, project_uri):
    # Procura na pasta workspaceStorage o workspace.json que bate com o URI
    home = os.path.expanduser("~")
    # Antigravity IDE ou Antigravity normal
    storage_candidates = [
        os.path.join(home, "AppData", "Roaming", "Antigravity IDE", "User", "workspaceStorage"),
        os.path.join(home, "AppData", "Roaming", "Antigravity", "User", "workspaceStorage"),
        os.path.join(home, "AppData", "Roaming", "antigravity", "User", "workspaceStorage"),
    ]
    norm_project_uri = normalize_uri(project_uri)
    for storage_dir in storage_candidates:
        if os.path.isdir(storage_dir):
            for name in os.listdir(storage_dir):
                ws_json = os.path.join(storage_dir, name, "workspace.json")
                if os.path.exists(ws_json):
                    try:
                        with open(ws_json, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        folder = data.get("folder") or data.get("workspace")
                        if folder and norm_project_uri in normalize_uri(folder):
                            return name
                    except Exception:
                        pass
    return None


# --- Processamento de Conversa ---
def translate_db_file(db_path, translations):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # 1. Atualiza trajectory_metadata_blob
        cur.execute("SELECT id, data FROM trajectory_metadata_blob")
        rows = cur.fetchall()
        for rid, blob in rows:
            if not blob:
                continue
            parsed = parse_protobuf(blob)
            modified = modify_fields(parsed, translations)
            new_blob = serialize_protobuf(modified)
            cur.execute("UPDATE trajectory_metadata_blob SET data = ? WHERE id = ?", (new_blob, rid))
            
        # 2. Atualiza texto na tabela steps
        cur.execute("SELECT idx, metadata, task_details, permissions FROM steps")
        steps = cur.fetchall()
        for idx, metadata, task_details, permissions in steps:
            updated = {}
            for col_name, raw_bytes in [("metadata", metadata), ("task_details", task_details), ("permissions", permissions)]:
                if raw_bytes:
                    try:
                        text = raw_bytes.decode('utf-8', errors='ignore')
                        new_text = text
                        for old_val, new_val in translations.items():
                            if old_val in new_text:
                                new_text = new_text.replace(old_val, new_val)
                        if new_text != text:
                            updated[col_name] = new_text.encode('utf-8')
                    except Exception:
                        pass
            if updated:
                set_clause = ", ".join([f"{col} = ?" for col in updated.keys()])
                params = list(updated.values()) + [idx]
                cur.execute(f"UPDATE steps SET {set_clause} WHERE idx = ?", params)
                
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"  x Erro ao traduzir banco {os.path.basename(db_path)}: {e}")
        if "locked" in str(e).lower() or "read-only" in str(e).lower():
            print("    DICA: Certifique-se de que a IDE Antigravity esteja completamente fechada para evitar bloqueios no banco de dados.")
        return False

# --- Fluxo Principal ---
def sync(mode, gemini_dir, backup_dir, translations):
    print(f"Modo: {mode.upper()}")
    
    if mode == "push":
        src_convs = os.path.join(gemini_dir, "conversations")
        src_brain = os.path.join(gemini_dir, "brain")
        dest_convs = os.path.join(backup_dir, "conversations")
        dest_brain = os.path.join(backup_dir, "brain")
    else:
        src_convs = os.path.join(backup_dir, "conversations")
        src_brain = os.path.join(backup_dir, "brain")
        dest_convs = os.path.join(gemini_dir, "conversations")
        dest_brain = os.path.join(gemini_dir, "brain")
        
    os.makedirs(dest_convs, exist_ok=True)
    os.makedirs(dest_brain, exist_ok=True)
    
    if not os.path.isdir(src_convs):
        print(f"Diretório de origem não existe: {src_convs}")
        return
        
    # Processa os bancos de dados
    success_count = 0
    for filename in os.listdir(src_convs):
        if filename.endswith(".pb") or (filename.endswith(".db") and not filename.endswith(("-shm", "-wal"))):
            convo_id = os.path.splitext(filename)[0]
            src_fpath = os.path.join(src_convs, filename)
            dest_fpath = os.path.join(dest_convs, filename)
            
            # Copia banco
            try:
                shutil.copy2(src_fpath, dest_fpath)
            except Exception as e:
                print(f"Erro ao copiar {filename}: {e}")
                continue
                
            # Traduz caminhos se for arquivo .db
            if filename.endswith(".db"):
                translate_db_file(dest_fpath, translations)
                
            # Copia pasta brain correspondente
            src_brain_folder = os.path.join(src_brain, convo_id)
            dest_brain_folder = os.path.join(dest_brain, convo_id)
            if os.path.isdir(src_brain_folder):
                try:
                    if os.path.exists(dest_brain_folder):
                        shutil.rmtree(dest_brain_folder)
                    shutil.copytree(src_brain_folder, dest_brain_folder)
                except Exception as e:
                    print(f"Erro ao copiar pasta brain {convo_id}: {e}")
            
            success_count += 1
            
    print(f"Sucesso: {success_count} conversas sincronizadas.")
    
    # Se puxamos alterações, removemos o index local para forçar refresh
    if mode == "pull" and success_count > 0:
        index_file = os.path.join(gemini_dir, "agyhub_summaries_proto.pb")
        if os.path.exists(index_file):
            try:
                os.remove(index_file)
                print("Índice agyhub_summaries_proto.pb removido para forçar atualização local.")
            except Exception:
                pass

def main():
    parser = argparse.ArgumentParser(description="Sincronizador de Conversas Antigravity 2.0")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--push", action="store_true", help="Exporta e normaliza do local para o backup")
    group.add_argument("--pull", action="store_true", help="Importa e localiza do backup para o local")
    parser.add_argument("--backup-dir", type=str, help="Caminho do repositório de backup")
    args = parser.parse_args()
    
    gemini_dir, config_dir = get_local_antigravity_paths()
    
    # 1. Detecta o projeto local
    proj = find_obsidian_project(config_dir)
    if not proj:
        print("Erro: Não foi possível detectar o projeto Obsidian local.")
        print("DICA: Abra a pasta do cofre no Antigravity 2.0 uma vez.")
        sys.exit(1)
        
    local_pid = proj["id"]
    local_uri = proj["uri"]
    local_uri_enc = urllib.parse.quote(local_uri, safe=":/")
    local_path = proj["path"].replace("\\", "/")
    
    # Resolve Workspace ID local
    local_ws_id = extract_workspace_id_from_local_dbs(gemini_dir)
    if not local_ws_id:
        local_ws_id = find_workspace_id_fallback(config_dir, local_uri)
    if not local_ws_id:
        # Fallback padrão gerado aleatoriamente se não encontrar nenhum
        local_ws_id = "fe29abba-eb39-44bf-8f95-ca286e02e5b4"
        
    # 2. Resolve o diretório do backup
    backup_dir = args.backup_dir
    if not backup_dir:
        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, "antigravity-backup"),
            os.path.join(home, ".gemini", "antigravity", "scratch", "antigravity-backup"),
            os.path.join(home, "Documents", "antigravity-backup"),
            os.path.join(home, "Desktop", "antigravity-backup")
        ]
        for c in candidates:
            if os.path.isdir(c):
                backup_dir = c
                break
    if not backup_dir or not os.path.isdir(backup_dir):
        print(f"Erro: Pasta de backup 'antigravity-backup' não encontrada. Informe via --backup-dir.")
        sys.exit(1)
        
    # 3. Define as traduções
    # Usamos placeholders universais intermediários no repositório de backup
    placeholder_uri = "{{WORKSPACE_URI}}"
    placeholder_uri_enc = "{{WORKSPACE_URI_ENC}}"
    placeholder_pid = "{{PROJECT_ID}}"
    placeholder_ws_id = "{{WORKSPACE_ID}}"
    placeholder_path = "{{WORKSPACE_PATH}}"
    
    if args.push:
        translations = {
            local_uri: placeholder_uri,
            local_uri_enc: placeholder_uri_enc,
            local_pid: placeholder_pid,
            local_ws_id: placeholder_ws_id,
            local_path: placeholder_path,
            local_path.replace("/", "\\"): placeholder_path
        }
        mode = "push"
    else:
        translations = {
            placeholder_uri: local_uri,
            placeholder_uri_enc: local_uri_enc,
            placeholder_pid: local_pid,
            placeholder_ws_id: local_ws_id,
            placeholder_path: local_path,
            placeholder_path.replace("/", "\\"): local_path.replace("/", "\\")
        }
        mode = "pull"
        
    print(f"Local Workspace Path: {local_path}")
    print(f"Local Project ID: {local_pid}")
    print(f"Local Workspace ID: {local_ws_id}")
    print(f"Backup Dir: {backup_dir}\n")
    
    sync(mode, gemini_dir, backup_dir, translations)

if __name__ == "__main__":
    main()
