// simple_parser.hpp - 单线程解析器
#pragma once
#include "cli_vault_types.hpp"
#include <fstream>
#include <sstream>
#include <string_view>

class SimpleParser {
public:
    struct ParseResult {
        std::vector<Link> links;  // [已注释links功能] 原用于存储解析出的链接
        std::vector<std::pair<std::string, Location>> tags;
        std::string title;
    };

    ParseResult parse(const fs::path& path, FileId current_id) {
        ParseResult result;

        std::ifstream file(path, std::ios::binary);
        if (!file) return result;

        std::string content((std::istreambuf_iterator<char>(file)),
                            std::istreambuf_iterator<char>());

        size_t pos = 0;
        if (content.size() >= 4 && content.substr(0, 3) == "---") {
            pos = parseFrontmatter(content, result, current_id);
        }

        parseBody(content, pos, result, current_id);

        return result;
    }

private:
    size_t parseFrontmatter(const std::string& content,
                           ParseResult& result,
                           FileId current_id) {
        size_t end = content.find("---", 3);
        if (end == std::string::npos) return 0;

        std::string_view yaml(content.data() + 3, end - 3);

        size_t tag_pos = yaml.find("tags:");
        if (tag_pos != std::string_view::npos) {
            parseYamlTags(yaml.substr(tag_pos), result, current_id);
        }

        size_t alias_pos = yaml.find("aliases:");
        if (alias_pos != std::string_view::npos) {
            // [已注释] aliases 相关
        }

        return end + 3;
    }

    void parseBody(const std::string& content,
                  size_t start,
                  ParseResult& result,
                  FileId current_id) {
        size_t i = start;
        uint32_t line = 1;
        uint32_t line_start = start;

        while (i < content.size()) {
            if (content[i] == '\n') {
                line++;
                line_start = i + 1;
            }

            // [已注释] === 检测 [[wikilink]] ===
            // if (i + 1 < content.size() &&
            //     content[i] == '[' && content[i+1] == '[') {
            //     auto [target, alias, len] = extractWikilink(content, i);
            //     if (len > 0) {
            //         Location loc{line, static_cast<uint16_t>(i - line_start),
            //                     static_cast<uint16_t>(len)};
            //         result.links.push_back({
            //             current_id, INVALID_ID, loc,
            //             LinkType::WikiLink, target
            //         });
            //         i += len;
            //         continue;
            //     }
            // }

            // 检测 #tag（但排除代码块内）
            if (content[i] == '#' && isValidTagStart(content, i)) {
                auto [tag_name, len] = extractTag(content, i);
                if (len > 0) {
                    Location loc{line, static_cast<uint16_t>(i - line_start),
                                static_cast<uint16_t>(len)};
                    result.tags.push_back({std::string(tag_name), loc});
                    i += len;
                    continue;
                }
            }

            i++;
        }
    }

    bool isValidTagStart(const std::string& s, size_t pos) {
        if (pos + 1 >= s.size()) return false;
        char c = s[pos + 1];
        return std::isalpha(c) || c == '_';
    }

    // [已注释] std::tuple<std::string_view, std::string_view, size_t>
    // extractWikilink(const std::string& s, size_t start) {
    //     size_t end = s.find("]]", start + 2);
    //     if (end == std::string::npos) return {"", "", 0};
    //     std::string_view inner(s.data() + start + 2, end - start - 2);
    //     size_t pipe = inner.find('|');
    //     if (pipe != std::string_view::npos) {
    //         return {inner.substr(0, pipe), inner.substr(pipe + 1), end - start + 2};
    //     }
    //     size_t hash = inner.find('#');
    //     if (hash != std::string_view::npos) {
    //         return {inner.substr(0, hash), "", end - start + 2};
    //     }
    //     return {inner, "", end - start + 2};
    // }

    std::pair<std::string_view, size_t>
    extractTag(const std::string& s, size_t start) {
        size_t i = start + 1;
        while (i < s.size() && (std::isalnum(s[i]) || s[i] == '-' || s[i] == '/')) {
            i++;
        }
        return {std::string_view(s.data() + start, i - start), i - start};
    }

    void parseYamlTags(std::string_view yaml, ParseResult& result, FileId id) {
        size_t bracket = yaml.find('[');
        if (bracket == std::string_view::npos) return;

        size_t end = yaml.find(']', bracket);
        if (end == std::string_view::npos) return;

        size_t pos = bracket + 1;
        while (pos < end) {
            while (pos < end && std::isspace(yaml[pos])) pos++;
            if (pos >= end) break;

            size_t comma = yaml.find(',', pos);
            if (comma == std::string_view::npos || comma > end) comma = end;

            std::string tag;
            for (size_t i = pos; i < comma; ++i) {
                if (yaml[i] != '"' && yaml[i] != '\'' && !std::isspace(yaml[i])) {
                    tag += yaml[i];
                }
            }

            if (!tag.empty()) {
                result.tags.push_back({tag, Location{0, 0, 0}});
            }

            pos = comma + 1;
        }
    }
};
