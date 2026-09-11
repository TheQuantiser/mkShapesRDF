#ifndef ZH4L_OUTPUTS_H
#define ZH4L_OUTPUTS_H

#include <ROOT/RVec.hxx>
#include <cmath>
#include <stdexcept>

namespace ZH4lOutputs {
template <typename T> T checkedWeight(T value) {
  if (!std::isfinite(value))
    throw std::runtime_error("ZH4l output weight is not finite; inspect correction validity and the weight recipe");
  return value;
}
template <typename T> ROOT::VecOps::RVec<T> checkedWeight(const ROOT::VecOps::RVec<T>& values) {
  for (auto value : values) checkedWeight(value);
  return values;
}
} // namespace ZH4lOutputs
#endif
