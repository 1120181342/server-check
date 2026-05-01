#!/usr/bin/env python3
import unittest
import tempfile
import os
import json
from ip_mapper import IPMapper, CloudServer, is_valid_ipv4


class TestIPMapper(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        self.temp_file.close()
        self.mapper = IPMapper(self.temp_file.name)
    
    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
    
    def test_is_valid_ipv4(self):
        self.assertTrue(is_valid_ipv4("192.168.1.1"))
        self.assertTrue(is_valid_ipv4("10.0.0.1"))
        self.assertTrue(is_valid_ipv4("255.255.255.255"))
        self.assertTrue(is_valid_ipv4("0.0.0.0"))
        
        self.assertFalse(is_valid_ipv4("256.0.0.1"))
        self.assertFalse(is_valid_ipv4("192.168.1"))
        self.assertFalse(is_valid_ipv4("192.168.1.1.1"))
        self.assertFalse(is_valid_ipv4("abc.def.ghi.jkl"))
        self.assertFalse(is_valid_ipv4(""))
    
    def test_add_server(self):
        result = self.mapper.add_server("vm-001", "192.168.1.10", "张三", "测试服务器")
        self.assertTrue(result)
        self.assertEqual(self.mapper.server_count, 1)
        
        server = self.mapper.get_server_by_id("vm-001")
        self.assertIsNotNone(server)
        self.assertEqual(server.server_id, "vm-001")
        self.assertEqual(server.ip, "192.168.1.10")
        self.assertEqual(server.user, "张三")
        self.assertEqual(server.description, "测试服务器")
        
        server_by_ip = self.mapper.get_server_by_ip("192.168.1.10")
        self.assertIsNotNone(server_by_ip)
        self.assertEqual(server_by_ip.server_id, "vm-001")
    
    def test_add_duplicate_server_id(self):
        self.mapper.add_server("vm-001", "192.168.1.10", "张三")
        result = self.mapper.add_server("vm-001", "192.168.1.20", "李四")
        self.assertFalse(result)
        self.assertEqual(self.mapper.server_count, 1)
    
    def test_add_duplicate_ip(self):
        self.mapper.add_server("vm-001", "192.168.1.10", "张三")
        result = self.mapper.add_server("vm-002", "192.168.1.10", "李四")
        self.assertFalse(result)
        self.assertEqual(self.mapper.server_count, 1)
    
    def test_add_invalid_ip(self):
        result = self.mapper.add_server("vm-001", "256.0.0.1", "张三")
        self.assertFalse(result)
        self.assertEqual(self.mapper.server_count, 0)
    
    def test_add_empty_id(self):
        result = self.mapper.add_server("", "192.168.1.10", "张三")
        self.assertFalse(result)
        self.assertEqual(self.mapper.server_count, 0)
    
    def test_add_empty_user(self):
        result = self.mapper.add_server("vm-001", "192.168.1.10", "")
        self.assertFalse(result)
        self.assertEqual(self.mapper.server_count, 0)
    
    def test_update_server(self):
        self.mapper.add_server("vm-001", "192.168.1.10", "张三", "旧描述")
        
        result = self.mapper.update_server("vm-001", user="李四", description="新描述")
        self.assertTrue(result)
        
        server = self.mapper.get_server_by_id("vm-001")
        self.assertEqual(server.user, "李四")
        self.assertEqual(server.description, "新描述")
        self.assertEqual(server.ip, "192.168.1.10")
    
    def test_update_server_ip(self):
        self.mapper.add_server("vm-001", "192.168.1.10", "张三")
        
        result = self.mapper.update_server("vm-001", ip="10.0.0.1")
        self.assertTrue(result)
        
        server = self.mapper.get_server_by_id("vm-001")
        self.assertEqual(server.ip, "10.0.0.1")
        
        old_ip_server = self.mapper.get_server_by_ip("192.168.1.10")
        self.assertIsNone(old_ip_server)
        
        new_ip_server = self.mapper.get_server_by_ip("10.0.0.1")
        self.assertEqual(new_ip_server.server_id, "vm-001")
    
    def test_update_nonexistent_server(self):
        result = self.mapper.update_server("vm-999", user="李四")
        self.assertFalse(result)
    
    def test_update_ip_conflict(self):
        self.mapper.add_server("vm-001", "192.168.1.10", "张三")
        self.mapper.add_server("vm-002", "192.168.1.20", "李四")
        
        result = self.mapper.update_server("vm-001", ip="192.168.1.20")
        self.assertFalse(result)
        
        server = self.mapper.get_server_by_id("vm-001")
        self.assertEqual(server.ip, "192.168.1.10")
    
    def test_delete_server(self):
        self.mapper.add_server("vm-001", "192.168.1.10", "张三")
        self.assertEqual(self.mapper.server_count, 1)
        
        result = self.mapper.delete_server("vm-001")
        self.assertTrue(result)
        self.assertEqual(self.mapper.server_count, 0)
        
        server = self.mapper.get_server_by_id("vm-001")
        self.assertIsNone(server)
        
        server_by_ip = self.mapper.get_server_by_ip("192.168.1.10")
        self.assertIsNone(server_by_ip)
    
    def test_delete_nonexistent_server(self):
        result = self.mapper.delete_server("vm-999")
        self.assertFalse(result)
    
    def test_get_servers_by_user(self):
        self.mapper.add_server("vm-001", "192.168.1.10", "张三")
        self.mapper.add_server("vm-002", "192.168.1.20", "张三")
        self.mapper.add_server("vm-003", "192.168.1.30", "李四")
        
        zhang_servers = self.mapper.get_servers_by_user("张三")
        self.assertEqual(len(zhang_servers), 2)
        server_ids = [s.server_id for s in zhang_servers]
        self.assertIn("vm-001", server_ids)
        self.assertIn("vm-002", server_ids)
        
        li_servers = self.mapper.get_servers_by_user("李四")
        self.assertEqual(len(li_servers), 1)
        self.assertEqual(li_servers[0].server_id, "vm-003")
        
        wang_servers = self.mapper.get_servers_by_user("王五")
        self.assertEqual(len(wang_servers), 0)
    
    def test_get_all_servers(self):
        self.mapper.add_server("vm-001", "192.168.1.10", "张三")
        self.mapper.add_server("vm-002", "192.168.1.20", "李四")
        
        all_servers = self.mapper.get_all_servers()
        self.assertEqual(len(all_servers), 2)
        server_ids = [s.server_id for s in all_servers]
        self.assertIn("vm-001", server_ids)
        self.assertIn("vm-002", server_ids)
    
    def test_search_servers(self):
        self.mapper.add_server("vm-001", "192.168.1.10", "张三", "测试服务器")
        self.mapper.add_server("vm-002", "10.0.0.1", "李四", "生产服务器")
        self.mapper.add_server("vm-003", "192.168.1.20", "王五", "开发服务器")
        
        results = self.mapper.search_servers("192.168")
        self.assertEqual(len(results), 2)
        ips = [s.ip for s in results]
        self.assertIn("192.168.1.10", ips)
        self.assertIn("192.168.1.20", ips)
        
        results = self.mapper.search_servers("张三")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].server_id, "vm-001")
        
        results = self.mapper.search_servers("测试")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].server_id, "vm-001")
        
        results = self.mapper.search_servers("vm-00")
        self.assertEqual(len(results), 3)
        
        results = self.mapper.search_servers("不存在")
        self.assertEqual(len(results), 0)
    
    def test_batch_add_servers(self):
        servers_data = [
            {"server_id": "vm-001", "ip": "192.168.1.10", "user": "张三"},
            {"server_id": "vm-002", "ip": "192.168.1.20", "user": "李四", "description": "测试"},
            {"server_id": "vm-001", "ip": "192.168.1.30", "user": "王五"},
            {"server_id": "", "ip": "192.168.1.40", "user": "赵六"},
        ]
        
        result = self.mapper.batch_add_servers(servers_data)
        self.assertEqual(result["success"], 2)
        self.assertEqual(result["failed"], 2)
        self.assertEqual(self.mapper.server_count, 2)
    
    def test_clear_all(self):
        self.mapper.add_server("vm-001", "192.168.1.10", "张三")
        self.mapper.add_server("vm-002", "192.168.1.20", "李四")
        self.assertEqual(self.mapper.server_count, 2)
        
        result = self.mapper.clear_all()
        self.assertTrue(result)
        self.assertEqual(self.mapper.server_count, 0)
        self.assertEqual(len(self.mapper.get_all_servers()), 0)
    
    def test_persistence(self):
        self.mapper.add_server("vm-001", "192.168.1.10", "张三", "测试服务器")
        self.mapper.add_server("vm-002", "192.168.1.20", "李四")
        
        new_mapper = IPMapper(self.temp_file.name)
        self.assertEqual(new_mapper.server_count, 2)
        
        server1 = new_mapper.get_server_by_id("vm-001")
        self.assertIsNotNone(server1)
        self.assertEqual(server1.ip, "192.168.1.10")
        self.assertEqual(server1.user, "张三")
        self.assertEqual(server1.description, "测试服务器")
        
        server2 = new_mapper.get_server_by_ip("192.168.1.20")
        self.assertIsNotNone(server2)
        self.assertEqual(server2.server_id, "vm-002")
    
    def test_cloud_server_to_dict(self):
        server = CloudServer("vm-001", "192.168.1.10", "张三", "测试")
        data = server.to_dict()
        self.assertEqual(data["server_id"], "vm-001")
        self.assertEqual(data["ip"], "192.168.1.10")
        self.assertEqual(data["user"], "张三")
        self.assertEqual(data["description"], "测试")
    
    def test_cloud_server_from_dict(self):
        data = {
            "server_id": "vm-001",
            "ip": "192.168.1.10",
            "user": "张三",
            "description": "测试"
        }
        server = CloudServer.from_dict(data)
        self.assertEqual(server.server_id, "vm-001")
        self.assertEqual(server.ip, "192.168.1.10")
        self.assertEqual(server.user, "张三")
        self.assertEqual(server.description, "测试")
    
    def test_cloud_server_from_dict_missing_description(self):
        data = {
            "server_id": "vm-001",
            "ip": "192.168.1.10",
            "user": "张三"
        }
        server = CloudServer.from_dict(data)
        self.assertEqual(server.description, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
