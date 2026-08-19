#!/usr/bin/env python3
"""
文档验证脚本
验证文档格式、大小和可读性
"""

import os
import sys
from pathlib import Path

def validate_document(file_path, max_size_mb=10):
    """
    验证文档文件
    
    Args:
        file_path: 文档文件路径
        max_size_mb: 最大文件大小（MB）
    
    Returns:
        tuple: (is_valid, message)
    """
    try:
        path = Path(file_path)
        
        # 检查文件是否存在
        if not path.exists():
            return False, f"文件不存在: {file_path}"
        
        # 检查文件大小
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            return False, f"文件过大: {file_size_mb:.2f}MB > {max_size_mb}MB"
        
        # 检查文件格式
        valid_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.markdown'}
        if path.suffix.lower() not in valid_extensions:
            return False, f"不支持的文件格式: {path.suffix}"
        
        return True, f"文档验证通过: {path.name} ({file_size_mb:.2f}MB)"
        
    except Exception as e:
        return False, f"验证过程中出错: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python validate_document.py <文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    is_valid, message = validate_document(file_path)
    
    if is_valid:
        print(f"✅ {message}")
        sys.exit(0)
    else:
        print(f"❌ {message}")
        sys.exit(1)
