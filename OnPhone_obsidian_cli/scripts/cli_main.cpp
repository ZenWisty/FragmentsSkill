// cli_main.cpp - 支持 tag/tags 子命令的 CLI 入口
#include "cli_vault_types.hpp"
#include "cli_simple_parser.hpp"
#include "cli_simple_index.hpp"
#include "cli_file_scanner.hpp"
#include <iostream>
#include <string>
#include <string_view>
#include <cstring>
#include <cstdlib>
#include <chrono>

using namespace std::string_view_literals;

// ============================
// 简易命令行参数解析
// ============================
struct CmdArgs {
    std::string subcmd;          // "tag" / "tags"
    std::string tag_name;        // --name
    std::string tag_path;        // --path (tags 命令的文件过滤)
    bool flag_total = false;
    bool flag_verbose = false;
    bool flag_counts = false;
    bool flag_sort_count = false;
};

CmdArgs parseArgs(int argc, char* argv[]) {
    CmdArgs args;

    if (argc < 2) {
        std::cerr << "用法: " << argv[0] << " <subcmd> [选项]\n";
        std::cerr << "子命令: tag, tags\n";
        std::exit(1);
    }

    args.subcmd = argv[1];

    // tag / tags 命令: 其余参数均为 --key=value 或 --flag 格式
    for (int i = 2; i < argc; ++i) {
        std::string_view arg = argv[i];

        if (arg == "--total") {
            args.flag_total = true;
        } else if (arg == "--verbose") {
            args.flag_verbose = true;
        } else if (arg == "--counts") {
            args.flag_counts = true;
        } else if (arg == "--sort=count") {
            args.flag_sort_count = true;
        } else if (arg.starts_with("--")) {
            size_t eq = arg.find('=');
            if (eq != std::string_view::npos) {
                std::string key(arg.substr(2, eq - 2));
                std::string val(arg.substr(eq + 1));
                if (key == "name")      args.tag_name = val;
                else if (key == "path") args.tag_path = val;
            }
        }
    }

    return args;
}

// ============================
// 主程序
// ============================
int main(int argc, char* argv[]) {
    auto args = parseArgs(argc, argv);

    if (args.subcmd == "tag") {
        // --- tag 模式：搜索含指定标签的文件 ---
        if (args.tag_name.empty()) {
            std::cerr << "错误: --name=<tag> 必须提供\n";
            return 1;
        }

        // 从环境变量获取 vault_path（由 shell 传入）
        const char* vault_c = std::getenv("OBSIDIAN_VAULT_PATH");
        if (!vault_c) {
            std::cerr << "错误: OBSIDIAN_VAULT_PATH 环境变量未设置\n";
            return 1;
        }
        fs::path vault_path = vault_c;

        auto start = std::chrono::steady_clock::now();

        FileScanner scanner;
        auto files = scanner.collect(vault_path);

        SimpleParser parser;
        SimpleIndex index;

        for (size_t i = 0; i < files.size(); ++i) {
            auto result = parser.parse(files[i], static_cast<FileId>(i));
            index.addFile(static_cast<FileId>(i), files[i].string(), result);
        }
        index.resolveLinks();

        auto end = std::chrono::steady_clock::now();
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
        (void)ms;  // 暂时不用耗时信息

        // 去掉开头的 # 如果用户带上了
        std::string tag_name = args.tag_name;
        if (!tag_name.empty() && tag_name[0] == '#') {
            tag_name = tag_name.substr(1);
        }

        auto files_with_tag = index.getFilesWithTag(tag_name);
        auto total_count = index.getTagOccurrenceCount(tag_name);

        if (args.flag_total) {
            std::cout << total_count << "\n";
            return 0;
        }

        std::cout << "Tag: #" << tag_name << "\n";
        std::cout << "Total Occurrences: " << total_count << "\n";

        if (args.flag_verbose && !files_with_tag.empty()) {
            std::cout << "\nFiles:\n";
            for (const auto& f : files_with_tag) {
                std::cout << f << "\n";
            }
        }

        return 0;
    }

    if (args.subcmd == "tags") {
        // --- tags 模式：列出标签 ---
        const char* vault_c = std::getenv("OBSIDIAN_VAULT_PATH");
        if (!vault_c) {
            std::cerr << "错误: OBSIDIAN_VAULT_PATH 环境变量未设置\n";
            return 1;
        }
        fs::path vault_path = vault_c;

        auto start = std::chrono::steady_clock::now();

        FileScanner scanner;
        auto files = scanner.collect(vault_path);

        SimpleParser parser;
        SimpleIndex index;

        for (size_t i = 0; i < files.size(); ++i) {
            auto result = parser.parse(files[i], static_cast<FileId>(i));
            index.addFile(static_cast<FileId>(i), files[i].string(), result);
        }
        index.resolveLinks();

        auto end = std::chrono::steady_clock::now();
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
        (void)ms;  // 暂时不用耗时信息

        auto tag_counts = index.getTagCounts();

        if (args.flag_total) {
            std::cout << tag_counts.size() << "\n";
            return 0;
        }

        if (args.flag_counts) {
            auto result = tag_counts;
            if (args.flag_sort_count) {
                std::sort(result.begin(), result.end(),
                         [](auto& a, auto& b) { return a.second > b.second; });
            }
            for (const auto& [name, count] : result) {
                std::cout << count << " #" << name << "\n";
            }
        } else {
            for (const auto& [name, count] : tag_counts) {
                std::cout << "#" << name << "\n";
            }
        }

        return 0;
    }

    // [已注释] === build 模式（预建索引，暂不使用） ===
    // if (args.subcmd == "build") {
    //     fs::path vault_path = args.vault_path;
    //     if (!fs::exists(vault_path)) {
    //         std::cerr << "路径不存在: " << vault_path << "\n";
    //         return 1;
    //     }
    //
    //     auto start = std::chrono::steady_clock::now();
    //
    //     std::cout << "扫描文件...\n";
    //     FileScanner scanner;
    //     auto files = scanner.collect(vault_path);
    //     std::cout << "找到 " << files.size() << " 个文件\n";
    //
    //     SimpleParser parser;
    //     SimpleIndex index;
    //
    //     for (size_t i = 0; i < files.size(); ++i) {
    //         auto result = parser.parse(files[i], static_cast<FileId>(i));
    //         index.addFile(static_cast<FileId>(i), files[i].string(), result);
    //         if ((i + 1) % 100 == 0) {
    //             std::cout << "已解析 " << (i + 1) << "/" << files.size() << "\n";
    //         }
    //     }
    //
    //     std::cout << "建立链接索引...\n";
    //     index.resolveLinks();
    //
    //     auto end = std::chrono::steady_clock::now();
    //     auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
    //
    //     std::cout << "\n=== 统计结果 ===\n";
    //     std::cout << "耗时: " << ms << "ms\n";
    //
    //     auto tag_counts = index.getTagCounts();
    //     std::cout << "\n前10个标签:\n";
    //     for (size_t i = 0; i < std::min(size_t(10), tag_counts.size()); ++i) {
    //         std::cout << "  #" << tag_counts[i].first
    //                   << ": " << tag_counts[i].second << "\n";
    //     }
    //
    //     auto orphans = index.getOrphans();
    //     std::cout << "\n孤立文件（无backlinks）: " << orphans.size() << "\n";
    //
    //     return 0;
    // }

    std::cerr << "未知子命令: " << args.subcmd << "\n";
    return 1;
}
