#!/usr/bin/env python3
import json
import os
from typing import Dict, List, Optional, Any, Iterator
from dataclasses import dataclass, asdict
from ip_classifier import is_valid_ipv4


@dataclass
class CloudServer:
    server_id: str
    ip: str
    user: str
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CloudServer":
        return cls(
            server_id=data["server_id"],
            ip=data["ip"],
            user=data["user"],
            description=data.get("description", "")
        )


class IPMapper:
    def __init__(self, data_file: Optional[str] = None):
        self._data_file = data_file or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ip_mapping.json"
        )
        self._servers: Dict[str, CloudServer] = {}
        self._ip_to_server: Dict[str, CloudServer] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        if os.path.exists(self._data_file):
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for server_data in data.get("servers", []):
                        server = CloudServer.from_dict(server_data)
                        self._servers[server.server_id] = server
                        self._ip_to_server[server.ip] = server
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"警告: 加载数据文件失败: {e}")
                self._servers = {}
                self._ip_to_server = {}
    
    def _save_data(self) -> None:
        data = {
            "servers": [server.to_dict() for server in self._servers.values()]
        }
        with open(self._data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_server(self, server_id: str, ip: str, user: str, description: str = "") -> bool:
        if not server_id.strip():
            return False
        
        if not is_valid_ipv4(ip):
            return False
        
        if not user.strip():
            return False
        
        if server_id in self._servers:
            return False
        
        if ip in self._ip_to_server:
            return False
        
        server = CloudServer(
            server_id=server_id.strip(),
            ip=ip.strip(),
            user=user.strip(),
            description=description.strip()
        )
        
        self._servers[server.server_id] = server
        self._ip_to_server[server.ip] = server
        self._save_data()
        return True
    
    def update_server(self, server_id: str, ip: Optional[str] = None, 
                      user: Optional[str] = None, description: Optional[str] = None) -> bool:
        if server_id not in self._servers:
            return False
        
        server = self._servers[server_id]
        
        if ip is not None:
            if not is_valid_ipv4(ip):
                return False
            if ip != server.ip and ip in self._ip_to_server:
                return False
            
            del self._ip_to_server[server.ip]
            server.ip = ip.strip()
            self._ip_to_server[server.ip] = server
        
        if user is not None:
            if not user.strip():
                return False
            server.user = user.strip()
        
        if description is not None:
            server.description = description.strip()
        
        self._save_data()
        return True
    
    def delete_server(self, server_id: str) -> bool:
        if server_id not in self._servers:
            return False
        
        server = self._servers[server_id]
        del self._servers[server_id]
        del self._ip_to_server[server.ip]
        self._save_data()
        return True
    
    def get_server_by_ip(self, ip: str) -> Optional[CloudServer]:
        ip = ip.strip()
        return self._ip_to_server.get(ip)
    
    def get_server_by_id(self, server_id: str) -> Optional[CloudServer]:
        server_id = server_id.strip()
        return self._servers.get(server_id)
    
    def get_servers_by_user(self, user: str) -> List[CloudServer]:
        user = user.strip()
        return [server for server in self._servers.values() if server.user == user]
    
    def get_all_servers(self) -> List[CloudServer]:
        return list(self._servers.values())
    
    def search_servers(self, keyword: str) -> List[CloudServer]:
        keyword = keyword.lower().strip()
        results = []
        for server in self._servers.values():
            if (keyword in server.server_id.lower() or
                keyword in server.ip.lower() or
                keyword in server.user.lower() or
                keyword in server.description.lower()):
                results.append(server)
        return results
    
    def batch_add_servers(self, servers_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        success_count = 0
        failed_count = 0
        errors = []
        
        for idx, server_data in enumerate(servers_data):
            try:
                server_id = server_data.get("server_id", "")
                ip = server_data.get("ip", "")
                user = server_data.get("user", "")
                description = server_data.get("description", "")
                
                if self.add_server(server_id, ip, user, description):
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append(f"第 {idx+1} 条: server_id={server_id}, ip={ip}")
            except Exception as e:
                failed_count += 1
                errors.append(f"第 {idx+1} 条: {str(e)}")
        
        return {
            "success": success_count,
            "failed": failed_count,
            "errors": errors
        }
    
    def import_from_csv(self, csv_file: str) -> Dict[str, Any]:
        import csv
        
        servers_data = []
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    server_data = {
                        "server_id": row.get("server_id", row.get("id", "")),
                        "ip": row.get("ip", row.get("ip_address", "")),
                        "user": row.get("user", row.get("owner", "")),
                        "description": row.get("description", row.get("desc", ""))
                    }
                    servers_data.append(server_data)
        except Exception as e:
            return {
                "success": 0,
                "failed": 0,
                "errors": [f"读取CSV文件失败: {str(e)}"]
            }
        
        return self.batch_add_servers(servers_data)
    
    def export_to_csv(self, csv_file: str) -> bool:
        import csv
        
        try:
            with open(csv_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f, 
                    fieldnames=["server_id", "ip", "user", "description"]
                )
                writer.writeheader()
                for server in self._servers.values():
                    writer.writerow(server.to_dict())
            return True
        except Exception:
            return False
    
    def clear_all(self) -> bool:
        try:
            self._servers.clear()
            self._ip_to_server.clear()
            self._save_data()
            return True
        except Exception:
            return False
    
    @property
    def data_file(self) -> str:
        return self._data_file
    
    @property
    def server_count(self) -> int:
        return len(self._servers)
