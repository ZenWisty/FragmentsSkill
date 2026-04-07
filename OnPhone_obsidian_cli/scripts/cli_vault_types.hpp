// vault_types.hpp - 基础类型定义
#pragma once
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <cstdint>
#include <filesystem>

namespace fs = std::filesystem;

// 文件ID：用32位节省内存
using FileId = uint32_t;
constexpr FileId INVALID_ID = UINT32_MAX;

// 位置信息（用于定位链接在文件中的位置）
struct Location {
    uint32_t line = 0;
    uint16_t col = 0;
    uint16_t len = 0;  // 链接文本长度
};

// 链接类型
enum class LinkType : uint8_t {
    WikiLink,      // [[Note]]
    WikiEmbed,     // ![[Image]]
    MarkdownLink,  // [text](url)
    TagInline,     // #tag
    TagFrontmatter // YAML 中的 tags
};

// 链接记录
struct Link {
    FileId source;      // 从哪个文件出发
    FileId target;      // 指向哪个文件（TAG时为INVALID_ID）
    Location loc;
    LinkType type;
    std::string text;   // 原始文本（如 "Other Note|别名"）
};

// 标签记录
struct Tag {
    std::string name;
    std::vector<FileId> files;  // 哪些文件有这个标签
    std::vector<Location> locations; // 出现位置
};

// 文件元数据
struct FileInfo {
    std::string path;           // 相对路径
    std::string title;          // 笔记标题
    uint64_t mtime = 0;         // 修改时间
    std::vector<Link> outlinks; // 出链
    // backlinks 单独存储在全局索引中
};