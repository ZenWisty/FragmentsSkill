// simple_index.hpp - 非并发索引
#pragma once
#include "cli_vault_types.hpp"
#include <unordered_map>
#include <algorithm>

class SimpleIndex {
public:
    // 添加文件及其解析结果
    void addFile(FileId id, const std::string& path,
                 const SimpleParser::ParseResult& parsed) {
        // 存储文件信息
        files_[id] = {path, parsed.title, 0, parsed.outlinks};

        // 建立路径到ID映射
        path_to_id_[path] = id;

        // 处理标签
        for (const auto& [tag_name, loc] : parsed.tags) {
            tags_[tag_name].files.push_back(id);
            tags_[tag_name].locations.push_back(loc);
        }
    }

    // [已注释] === backlinks 相关（暂不使用）===
    // void resolveLinks() {
    //     for (auto& [id, file] : files_) {
    //         for (auto& link : file.outlinks) {
    //             auto it = path_to_id_.find(normalizePath(link.text));
    //             if (it != path_to_id_.end()) {
    //                 link.target = it->second;
    //                 backlinks_[it->second].push_back(link);
    //             } else {
    //                 unresolved_.push_back({id, link.text});
    //             }
    //         }
    //     }
    // }

    // 查询接口
    // [已注释] std::vector<Link> getBacklinks(FileId target) const {
    //     auto it = backlinks_.find(target);
    //     if (it != backlinks_.end()) return it->second;
    //     return {};
    // }

    // 返回含指定标签的所有文件路径（去重）
    std::vector<std::string> getFilesWithTag(const std::string& tag_name) const {
        std::vector<std::string> result;
        auto it = tags_.find(tag_name);
        if (it == tags_.end()) return result;
        for (FileId fid : it->second.files) {
            auto fIt = files_.find(fid);
            if (fIt != files_.end()) {
                result.push_back(fIt->second.path);
            }
        }
        return result;
    }

    // 返回指定标签的出现总次数（所有文件中该标签的 location 数之和）
    size_t getTagOccurrenceCount(const std::string& tag_name) const {
        auto it = tags_.find(tag_name);
        if (it == tags_.end()) return 0;
        return it->second.locations.size();
    }

    std::vector<std::pair<std::string, size_t>> getTagCounts() const {
        std::vector<std::pair<std::string, size_t>> result;
        for (const auto& [name, tag] : tags_) {
            result.push_back({name, tag.locations.size()});
        }
        std::sort(result.begin(), result.end(),
                 [](auto& a, auto& b) { return a.second > b.second; });
        return result;
    }

    // [已注释] std::vector<FileId> getOrphans() const {
    //     std::vector<FileId> result;
    //     for (const auto& [id, file] : files_) {
    //         if (backlinks_.find(id) == backlinks_.end()) {
    //             result.push_back(id);
    //         }
    //     }
    //     return result;
    // }

private:
    std::unordered_map<FileId, FileInfo> files_;
    std::unordered_map<std::string, FileId> path_to_id_;
    // [已注释] std::unordered_map<FileId, std::vector<Link>> backlinks_;
    std::unordered_map<std::string, Tag> tags_;
    // [已注释] std::vector<std::pair<FileId, std::string>> unresolved_;

    // [已注释] std::string normalizePath(const std::string& link_text) {
    //     std::string result = link_text;
    //     if (result.size() > 3 && result.substr(result.size() - 3) == ".md") {
    //         return result;
    //     }
    //     return result + ".md";
    // }
};
