import bisect
import ipaddress
from typing import List, Tuple, Iterator, Optional


def ip_to_int(ip_str: str) -> int:
    octets = ip_str.split('.')
    return (int(octets[0]) << 24) | (int(octets[1]) << 16) | (int(octets[2]) << 8) | int(octets[3])


def is_valid_ipv4(ip_str: str) -> bool:
    parts = ip_str.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        try:
            num = int(part)
            if num < 0 or num > 255:
                return False
        except ValueError:
            return False
    return True


def parse_cidr(cidr: str) -> Tuple[int, int]:
    ip_part, prefix_part = cidr.split('/', 1)
    prefix = int(prefix_part)
    base_ip = ip_to_int(ip_part)
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    start_ip = base_ip & mask
    end_ip = start_ip | (0xFFFFFFFF >> prefix)
    return start_ip, end_ip


def load_cidr_list(cidr_list: List[str]) -> List[Tuple[int, int]]:
    ranges = []
    for cidr in cidr_list:
        try:
            ranges.append(parse_cidr(cidr))
        except (ValueError, IndexError):
            continue
    ranges.sort(key=lambda x: x[0])
    merged = []
    for start, end in ranges:
        if not merged:
            merged.append([start, end])
        else:
            last_start, last_end = merged[-1]
            if start <= last_end + 1:
                merged[-1][1] = max(last_end, end)
            else:
                merged.append([start, end])
    return [(s, e) for s, e in merged]


def load_cidr_from_file(file_path: str) -> List[Tuple[int, int]]:
    cidr_list = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                cidr_list.append(line)
    return load_cidr_list(cidr_list)


class IPClassifier:
    def __init__(self, china_ranges: Optional[List[Tuple[int, int]]] = None):
        self._china_ranges = china_ranges or []
        self._start_ips = [r[0] for r in self._china_ranges] if self._china_ranges else []
    
    def load_china_cidrs(self, cidr_list: List[str]) -> None:
        self._china_ranges = load_cidr_list(cidr_list)
        self._start_ips = [r[0] for r in self._china_ranges]
    
    def load_china_cidrs_from_file(self, file_path: str) -> None:
        self._china_ranges = load_cidr_from_file(file_path)
        self._start_ips = [r[0] for r in self._china_ranges]
    
    def is_china_ip(self, ip_str: str) -> bool:
        if not is_valid_ipv4(ip_str):
            return False
        try:
            ip_int = ip_to_int(ip_str)
        except (ValueError, IndexError):
            return False
        
        if not self._start_ips:
            return False
        
        idx = bisect.bisect_right(self._start_ips, ip_int) - 1
        
        if idx >= 0:
            start, end = self._china_ranges[idx]
            return start <= ip_int <= end
        
        return False
    
    def classify(self, ips: Iterator[str]) -> Tuple[List[str], List[str]]:
        china_ips = []
        foreign_ips = []
        
        for ip in ips:
            ip = ip.strip()
            if not ip:
                continue
            if self.is_china_ip(ip):
                china_ips.append(ip)
            else:
                foreign_ips.append(ip)
        
        return china_ips, foreign_ips
    
    def classify_iter(self, ips: Iterator[str]) -> Iterator[Tuple[str, bool]]:
        for ip in ips:
            ip = ip.strip()
            if not ip:
                continue
            yield ip, self.is_china_ip(ip)
    
    def classify_to_files(self, 
                          input_file: str, 
                          china_output: str, 
                          foreign_output: str,
                          encoding: str = 'utf-8') -> Tuple[int, int]:
        china_count = 0
        foreign_count = 0
        
        with open(input_file, 'r', encoding=encoding) as infile, \
             open(china_output, 'w', encoding=encoding) as china_file, \
             open(foreign_output, 'w', encoding=encoding) as foreign_file:
            
            for line in infile:
                ip = line.strip()
                if not ip:
                    continue
                
                if self.is_china_ip(ip):
                    china_file.write(ip + '\n')
                    china_count += 1
                else:
                    foreign_file.write(ip + '\n')
                    foreign_count += 1
        
        return china_count, foreign_count


DEFAULT_CHINA_CIDRS = [
    "1.0.1.0/24",
    "1.0.2.0/23",
    "1.0.8.0/21",
    "1.0.32.0/19",
    "1.1.0.0/22",
    "1.1.8.0/21",
    "1.1.32.0/19",
    "1.2.0.0/16",
    "1.3.0.0/16",
    "1.4.0.0/14",
    "1.8.0.0/13",
    "1.16.0.0/12",
    "1.32.0.0/11",
    "1.56.0.0/13",
    "1.64.0.0/10",
    "1.128.0.0/9",
    "14.0.0.0/11",
    "14.32.0.0/13",
    "14.96.0.0/11",
    "14.128.0.0/10",
    "14.192.0.0/12",
    "14.208.0.0/12",
    "27.0.0.0/13",
    "27.16.0.0/12",
    "27.32.0.0/11",
    "27.96.0.0/11",
    "27.128.0.0/11",
    "27.176.0.0/12",
    "27.192.0.0/12",
    "27.224.0.0/11",
    "36.0.0.0/11",
    "36.40.0.0/13",
    "36.48.0.0/12",
    "36.96.0.0/11",
    "36.128.0.0/10",
    "36.192.0.0/11",
    "36.224.0.0/12",
    "36.240.0.0/12",
    "39.0.0.0/10",
    "39.64.0.0/11",
    "39.96.0.0/12",
    "39.128.0.0/10",
    "40.0.0.0/9",
    "42.0.0.0/8",
    "43.224.0.0/12",
    "43.240.0.0/12",
    "45.112.0.0/12",
    "45.120.0.0/13",
    "45.192.0.0/11",
    "47.92.0.0/14",
    "47.96.0.0/11",
    "47.104.0.0/13",
    "47.112.0.0/12",
    "47.120.0.0/13",
    "47.128.0.0/10",
    "49.4.0.0/14",
    "49.8.0.0/13",
    "49.16.0.0/12",
    "49.32.0.0/11",
    "49.64.0.0/11",
    "49.112.0.0/12",
    "49.128.0.0/10",
    "49.192.0.0/11",
    "49.224.0.0/12",
    "49.240.0.0/12",
    "52.80.0.0/12",
    "52.192.0.0/11",
    "54.222.0.0/15",
    "54.248.0.0/13",
    "58.0.0.0/13",
    "58.16.0.0/12",
    "58.32.0.0/11",
    "58.64.0.0/12",
    "58.80.0.0/12",
    "58.96.0.0/12",
    "58.112.0.0/12",
    "58.128.0.0/12",
    "58.144.0.0/12",
    "58.160.0.0/12",
    "58.192.0.0/12",
    "58.208.0.0/12",
    "58.240.0.0/12",
    "59.32.0.0/11",
    "59.64.0.0/12",
    "59.77.0.0/16",
    "59.78.0.0/15",
    "59.80.0.0/12",
    "59.108.0.0/14",
    "59.172.0.0/14",
    "59.176.0.0/12",
    "59.192.0.0/10",
    "60.0.0.0/11",
    "60.48.0.0/12",
    "60.160.0.0/11",
    "60.192.0.0/10",
    "60.240.0.0/12",
    "61.4.0.0/14",
    "61.8.0.0/13",
    "61.16.0.0/12",
    "61.32.0.0/11",
    "61.128.0.0/10",
    "61.160.0.0/11",
    "61.176.0.0/12",
    "61.184.0.0/13",
    "61.232.0.0/12",
    "61.240.0.0/12",
    "101.0.0.0/13",
    "101.16.0.0/12",
    "101.32.0.0/11",
    "101.64.0.0/10",
    "101.128.0.0/10",
    "101.192.0.0/11",
    "101.224.0.0/11",
    "106.0.0.0/12",
    "106.16.0.0/13",
    "106.40.0.0/13",
    "106.80.0.0/12",
    "106.112.0.0/12",
    "106.120.0.0/13",
    "106.224.0.0/12",
    "106.240.0.0/12",
    "110.0.0.0/11",
    "110.40.0.0/13",
    "110.48.0.0/12",
    "110.64.0.0/10",
    "110.128.0.0/9",
    "111.0.0.0/12",
    "111.16.0.0/12",
    "111.32.0.0/11",
    "111.112.0.0/12",
    "111.128.0.0/10",
    "111.192.0.0/12",
    "111.224.0.0/12",
    "112.0.0.0/10",
    "112.64.0.0/12",
    "112.80.0.0/12",
    "112.96.0.0/12",
    "112.112.0.0/12",
    "112.128.0.0/10",
    "112.192.0.0/11",
    "112.224.0.0/11",
    "113.0.0.0/10",
    "113.64.0.0/10",
    "113.128.0.0/9",
    "114.16.0.0/12",
    "114.24.0.0/13",
    "114.32.0.0/11",
    "114.64.0.0/10",
    "114.128.0.0/10",
    "114.192.0.0/11",
    "114.224.0.0/11",
    "115.0.0.0/12",
    "115.16.0.0/13",
    "115.32.0.0/11",
    "115.48.0.0/12",
    "115.60.0.0/14",
    "115.64.0.0/11",
    "115.100.0.0/14",
    "115.120.0.0/13",
    "115.128.0.0/11",
    "115.168.0.0/13",
    "115.176.0.0/12",
    "115.192.0.0/11",
    "115.224.0.0/11",
    "116.0.0.0/11",
    "116.48.0.0/12",
    "116.64.0.0/10",
    "116.128.0.0/10",
    "116.192.0.0/11",
    "116.224.0.0/12",
    "116.242.0.0/15",
    "116.244.0.0/14",
    "116.248.0.0/13",
    "117.8.0.0/13",
    "117.16.0.0/12",
    "117.32.0.0/11",
    "117.48.0.0/12",
    "117.64.0.0/10",
    "117.128.0.0/9",
    "118.24.0.0/13",
    "118.32.0.0/11",
    "118.64.0.0/10",
    "118.112.0.0/12",
    "118.120.0.0/13",
    "118.128.0.0/12",
    "118.144.0.0/12",
    "118.180.0.0/14",
    "118.192.0.0/12",
    "118.212.0.0/14",
    "118.224.0.0/12",
    "118.248.0.0/13",
    "119.0.0.0/11",
    "119.32.0.0/11",
    "119.60.0.0/14",
    "119.78.0.0/15",
    "119.80.0.0/12",
    "119.96.0.0/12",
    "119.112.0.0/12",
    "119.120.0.0/13",
    "119.128.0.0/10",
    "119.192.0.0/11",
    "119.224.0.0/12",
    "119.248.0.0/13",
    "120.0.0.0/10",
    "120.64.0.0/12",
    "120.80.0.0/12",
    "120.92.0.0/14",
    "120.128.0.0/10",
    "120.192.0.0/10",
    "121.0.0.0/10",
    "121.64.0.0/10",
    "121.128.0.0/10",
    "121.192.0.0/10",
    "122.0.0.0/11",
    "122.40.0.0/14",
    "122.48.0.0/16",
    "122.51.0.0/16",
    "122.64.0.0/11",
    "122.96.0.0/11",
    "122.128.0.0/10",
    "122.192.0.0/11",
    "122.224.0.0/12",
    "122.240.0.0/12",
    "123.0.0.0/10",
    "123.64.0.0/11",
    "123.96.0.0/12",
    "123.128.0.0/9",
    "124.0.0.0/10",
    "124.64.0.0/10",
    "124.128.0.0/10",
    "124.192.0.0/10",
    "125.0.0.0/10",
    "125.64.0.0/10",
    "125.76.0.0/13",
    "125.84.0.0/14",
    "125.88.0.0/13",
    "125.104.0.0/13",
    "125.112.0.0/12",
    "125.120.0.0/13",
    "125.128.0.0/10",
    "125.192.0.0/10",
    "180.76.0.0/16",
    "180.78.0.0/15",
    "180.80.0.0/12",
    "180.96.0.0/11",
    "180.128.0.0/10",
    "180.192.0.0/10",
    "182.48.0.0/12",
    "182.64.0.0/10",
    "182.112.0.0/12",
    "182.128.0.0/10",
    "182.240.0.0/12",
    "183.0.0.0/10",
    "183.64.0.0/10",
    "183.128.0.0/10",
    "183.192.0.0/11",
    "202.0.0.0/8",
    "203.0.0.0/8",
    "210.0.0.0/7",
    "218.0.0.0/7",
    "220.152.0.0/13",
    "220.160.0.0/11",
    "220.192.0.0/11",
    "220.228.0.0/14",
    "220.248.0.0/13",
    "220.252.0.0/14",
    "221.0.0.0/12",
    "221.12.0.0/14",
    "221.192.0.0/14",
    "221.200.0.0/13",
    "221.208.0.0/12",
    "221.224.0.0/12",
    "221.232.0.0/13",
    "221.240.0.0/12",
    "222.0.0.0/11",
    "222.32.0.0/11",
    "222.64.0.0/10",
    "222.128.0.0/10",
    "222.160.0.0/13",
    "222.168.0.0/13",
    "222.176.0.0/12",
    "222.192.0.0/11",
    "222.224.0.0/12",
    "222.240.0.0/12",
    "223.0.0.0/12",
    "223.16.0.0/12",
    "223.32.0.0/11",
    "223.64.0.0/10",
    "223.128.0.0/9",
]


def create_default_classifier() -> IPClassifier:
    classifier = IPClassifier()
    classifier.load_china_cidrs(DEFAULT_CHINA_CIDRS)
    return classifier
