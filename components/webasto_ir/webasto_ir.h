#pragma once
// Standalone CARRIER_AC128 wire codec. See docs/ir-protocol.md for provenance.
#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace webasto_ir {
using Frame = std::array<uint8_t, 16>;

inline uint8_t checksum(const Frame &f, size_t start) {
  unsigned sum = f[start + 7] & 15;
  for (size_t i = start; i < start + 7; ++i) sum += (f[i] >> 4) + (f[i] & 15);
  return sum & 15;
}
inline bool valid(const Frame &f) {
  return f[0] == 0x16 && checksum(f, 0) == (f[7] >> 4) &&
         checksum(f, 8) == (f[15] >> 4);
}
inline int hex_digit(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  return -1;
}
inline bool parse(const std::string &s, Frame &f) {
  // Spaces only between complete bytes, exactly sixteen bytes.
  size_t count = 0;
  int high = -1;
  f.fill(0);
  for (char c : s) {
    if (c == ' ' && high == -1) continue;
    int digit = hex_digit(c);
    if (digit < 0 || count >= 16) return false;
    if (high == -1) high = digit;
    else { f[count++] = (high << 4) | digit; high = -1; }
  }
  return count == 16 && high == -1 && valid(f);
}
inline std::string format(const Frame &f) {
  constexpr char HEX[] = "0123456789ABCDEF";
  std::string result;
  result.reserve(47);
  for (size_t i = 0; i < 16; ++i) {
    if (i) result += ' ';
    result += HEX[f[i] >> 4]; result += HEX[f[i] & 15];
  }
  return result;
}
inline bool matches(int64_t value, int nominal, int percent) {
  return value * 100 >= nominal * (100 - percent) &&
         value * 100 <= nominal * (100 + percent);
}
inline bool decode(const std::vector<int32_t> &raw, Frame &f) {
  if (raw.size() != 267) return false;
  for (size_t i = 0; i < raw.size(); ++i)
    if (!raw[i] || (raw[i] > 0) != (i % 2 == 0)) return false;
  constexpr size_t indices[] = {0,1,130,131,132,133,134,135,264,265,266};
  constexpr int nominals[] = {4600,2600,340,20600,4600,6700,9300,5000,340,20600,4600};
  for (size_t i = 0; i < 11; ++i) {
    int64_t v = raw[indices[i]];
    if (v < 0) v = -v;
    if (!matches(v, nominals[i], nominals[i] == 340 ? 35 : 25)) return false;
  }
  f.fill(0);
  for (size_t section = 0; section < 2; ++section) {
    size_t start = section ? 136 : 2;
    for (size_t bit = 0; bit < 64; ++bit) {
      size_t i = start + bit * 2;
      if (!matches(raw[i], 340, 35)) return false;
      int64_t total = static_cast<int64_t>(raw[i]) - raw[i + 1];
      bool zero = matches(total, 740, 20), one = matches(total, 1340, 20);
      if (zero == one) return false;
      if (one) f[section * 8 + bit / 8] |= 1 << (bit % 8);
    }
  }
  return valid(f);
}
inline std::vector<int32_t> encode(const Frame &f) {
  if (!valid(f)) return {};
  std::vector<int32_t> raw;
  raw.reserve(267);
  for (size_t section = 0; section < 2; ++section) {
    raw.push_back(section ? 9300 : 4600); raw.push_back(section ? -5000 : -2600);
    for (size_t i = section * 8; i < section * 8 + 8; ++i)
      for (unsigned bit = 0; bit < 8; ++bit) {
        raw.push_back(340); raw.push_back(f[i] & (1 << bit) ? -1000 : -400);
      }
    raw.push_back(340); raw.push_back(-20600); raw.push_back(4600);
    if (!section) raw.push_back(-6700);
  }
  return raw;
}
}  // namespace webasto_ir
