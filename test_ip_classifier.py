#!/usr/bin/env python3
import unittest
import tempfile
import os
from ip_classifier import (
    ip_to_int, is_valid_ipv4, parse_cidr,
    load_cidr_list, load_cidr_from_file,
    IPClassifier, create_default_classifier,
    DEFAULT_CHINA_CIDRS
)


class TestIPClassifier(unittest.TestCase):
    
    def test_ip_to_int(self):
        self.assertEqual(ip_to_int("0.0.0.0"), 0)
        self.assertEqual(ip_to_int("255.255.255.255"), 0xFFFFFFFF)
        self.assertEqual(ip_to_int("192.168.1.1"), 0xC0A80101)
        self.assertEqual(ip_to_int("1.1.1.1"), 0x01010101)
    
    def test_is_valid_ipv4(self):
        self.assertTrue(is_valid_ipv4("0.0.0.0"))
        self.assertTrue(is_valid_ipv4("255.255.255.255"))
        self.assertTrue(is_valid_ipv4("192.168.1.1"))
        self.assertTrue(is_valid_ipv4("1.1.1.1"))
        
        self.assertFalse(is_valid_ipv4("256.0.0.0"))
        self.assertFalse(is_valid_ipv4("0.0.0"))
        self.assertFalse(is_valid_ipv4("0.0.0.0.0"))
        self.assertFalse(is_valid_ipv4("abc.def.ghi.jkl"))
        self.assertFalse(is_valid_ipv4(""))
        self.assertFalse(is_valid_ipv4("192.168.1"))
    
    def test_parse_cidr(self):
        start, end = parse_cidr("192.168.1.0/24")
        self.assertEqual(start, 0xC0A80100)
        self.assertEqual(end, 0xC0A801FF)
        
        start, end = parse_cidr("10.0.0.0/8")
        self.assertEqual(start, 0x0A000000)
        self.assertEqual(end, 0x0AFFFFFF)
        
        start, end = parse_cidr("172.16.0.0/12")
        self.assertEqual(start, 0xAC100000)
        self.assertEqual(end, 0xAC1FFFFF)
    
    def test_load_cidr_list(self):
        cidrs = ["192.168.1.0/24", "192.168.2.0/24", "10.0.0.0/8"]
        ranges = load_cidr_list(cidrs)
        
        self.assertEqual(len(ranges), 2)
        
        sorted_ranges = sorted(ranges, key=lambda x: x[0])
        self.assertEqual(sorted_ranges[0][0], 0x0A000000)
        self.assertEqual(sorted_ranges[0][1], 0x0AFFFFFF)
        
        self.assertEqual(sorted_ranges[1][0], 0xC0A80100)
        self.assertEqual(sorted_ranges[1][1], 0xC0A802FF)
    
    def test_load_cidr_from_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("# 注释行\n")
            f.write("192.168.1.0/24\n")
            f.write("10.0.0.0/8\n")
            f.write("\n")
            f.write("172.16.0.0/12\n")
            temp_path = f.name
        
        try:
            ranges = load_cidr_from_file(temp_path)
            self.assertEqual(len(ranges), 3)
        finally:
            os.unlink(temp_path)
    
    def test_ip_classifier_basic(self):
        classifier = IPClassifier()
        classifier.load_china_cidrs(["192.168.1.0/24", "10.0.0.0/8"])
        
        self.assertTrue(classifier.is_china_ip("192.168.1.1"))
        self.assertTrue(classifier.is_china_ip("10.0.0.1"))
        self.assertFalse(classifier.is_china_ip("172.16.0.1"))
        self.assertFalse(classifier.is_china_ip("8.8.8.8"))
    
    def test_classify_method(self):
        classifier = IPClassifier()
        classifier.load_china_cidrs(["192.168.1.0/24", "10.0.0.0/8"])
        
        ips = ["192.168.1.1", "10.0.0.1", "8.8.8.8", "1.1.1.1", "192.168.1.100"]
        china, foreign = classifier.classify(iter(ips))
        
        self.assertIn("192.168.1.1", china)
        self.assertIn("10.0.0.1", china)
        self.assertIn("192.168.1.100", china)
        self.assertEqual(len(china), 3)
        
        self.assertIn("8.8.8.8", foreign)
        self.assertIn("1.1.1.1", foreign)
        self.assertEqual(len(foreign), 2)
    
    def test_classify_iter(self):
        classifier = IPClassifier()
        classifier.load_china_cidrs(["192.168.1.0/24"])
        
        ips = ["192.168.1.1", "8.8.8.8", "192.168.1.100"]
        results = list(classifier.classify_iter(iter(ips)))
        
        self.assertEqual(results, [
            ("192.168.1.1", True),
            ("8.8.8.8", False),
            ("192.168.1.100", True)
        ])
    
    def test_classify_to_files(self):
        classifier = IPClassifier()
        classifier.load_china_cidrs(["192.168.1.0/24", "10.0.0.0/8"])
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as infile:
            infile.write("192.168.1.1\n")
            infile.write("10.0.0.1\n")
            infile.write("8.8.8.8\n")
            infile.write("1.1.1.1\n")
            infile.write("192.168.1.100\n")
            input_path = infile.name
        
        china_path = tempfile.mktemp(suffix='.txt')
        foreign_path = tempfile.mktemp(suffix='.txt')
        
        try:
            china_count, foreign_count = classifier.classify_to_files(
                input_path, china_path, foreign_path
            )
            
            self.assertEqual(china_count, 3)
            self.assertEqual(foreign_count, 2)
            
            with open(china_path, 'r', encoding='utf-8') as f:
                china_ips = [line.strip() for line in f if line.strip()]
            self.assertEqual(len(china_ips), 3)
            self.assertIn("192.168.1.1", china_ips)
            self.assertIn("10.0.0.1", china_ips)
            self.assertIn("192.168.1.100", china_ips)
            
            with open(foreign_path, 'r', encoding='utf-8') as f:
                foreign_ips = [line.strip() for line in f if line.strip()]
            self.assertEqual(len(foreign_ips), 2)
            self.assertIn("8.8.8.8", foreign_ips)
            self.assertIn("1.1.1.1", foreign_ips)
        finally:
            os.unlink(input_path)
            if os.path.exists(china_path):
                os.unlink(china_path)
            if os.path.exists(foreign_path):
                os.unlink(foreign_path)
    
    def test_default_classifier(self):
        classifier = create_default_classifier()
        
        self.assertTrue(classifier.is_china_ip("223.5.5.5"))
        self.assertTrue(classifier.is_china_ip("114.114.114.114"))
        self.assertTrue(classifier.is_china_ip("180.76.76.76"))
        
        self.assertFalse(classifier.is_china_ip("8.8.8.8"))
        self.assertFalse(classifier.is_china_ip("1.1.1.1"))
        self.assertFalse(classifier.is_china_ip("8.8.4.4"))
    
    def test_empty_classifier(self):
        classifier = IPClassifier()
        self.assertFalse(classifier.is_china_ip("8.8.8.8"))
        self.assertFalse(classifier.is_china_ip("223.5.5.5"))
        
        china, foreign = classifier.classify(iter(["8.8.8.8", "223.5.5.5"]))
        self.assertEqual(len(china), 0)
        self.assertEqual(len(foreign), 2)
    
    def test_invalid_ips(self):
        classifier = create_default_classifier()
        
        self.assertFalse(classifier.is_china_ip(""))
        self.assertFalse(classifier.is_china_ip("invalid"))
        self.assertFalse(classifier.is_china_ip("256.0.0.1"))
        self.assertFalse(classifier.is_china_ip("192.168.1"))
        
        ips = ["8.8.8.8", "", "invalid", "223.5.5.5", "256.0.0.1"]
        china, foreign = classifier.classify(iter(ips))
        self.assertIn("223.5.5.5", china)
        self.assertEqual(len(china), 1)
        self.assertIn("8.8.8.8", foreign)
        self.assertEqual(len(foreign), 4)
    
    def test_cidr_merging(self):
        cidrs = [
            "192.168.0.0/23",
            "192.168.2.0/23",
            "192.168.4.0/22"
        ]
        ranges = load_cidr_list(cidrs)
        
        self.assertEqual(len(ranges), 1)
        start, end = ranges[0]
        
        expected_start = 0xC0A80000
        expected_end = 0xC0A807FF
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)


if __name__ == '__main__':
    unittest.main(verbosity=2)
