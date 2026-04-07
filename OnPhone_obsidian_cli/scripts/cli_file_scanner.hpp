// file_scanner.hpp - 单线程文件扫描
#pragma once
#include <filesystem>
#include <vector>
#include <string>
#include <functional>

namespace fs = std::filesystem;

class FileScanner {
public:
    using FileHandler = std::function<void(const fs::path&)>;
    
    // 递归遍历目录，找到所有 .md 文件
    void scan(const fs::path& root, FileHandler handler) {
        if (!fs::exists(root)) return;
        
        // 递归_directory_iterator
        for (const auto& entry : fs::recursive_directory_iterator(root)) {
            if (entry.is_regular_file() && 
                entry.path().extension() == ".md") {
                handler(entry.path());
            }
        }
    }
    
    // 批量收集版本（更省内存）
    std::vector<fs::path> collect(const fs::path& root) {
        std::vector<fs::path> files;
        files.reserve(1000);  // 预分配避免频繁扩容
        
        scan(root, [&files](const fs::path& p) {
            files.push_back(p);
        });
        
        return files;
    }
};