#include "mathlib.h"
#include <stdexcept>
#include <limits>

namespace mathlib {

int add(int a, int b) {
    if (b > 0 && a > std::numeric_limits<int>::max() - b)
        throw std::overflow_error("Integer overflow in addition");
    if (b < 0 && a < std::numeric_limits<int>::min() - b)
        throw std::overflow_error("Integer underflow in addition");
    return a + b;
}

int subtract(int a, int b) { return add(a, -b); }

int multiply(int a, int b) {
    if (a == 0 || b == 0) return 0;
    int result = a * b;
    if (result / a != b)
        throw std::overflow_error("Integer overflow in multiplication");
    return result;
}

double divide(int a, int b) {
    if (b == 0) throw std::invalid_argument("Division by zero");
    return static_cast<double>(a) / static_cast<double>(b);
}

bool is_even(int n) { return n % 2 == 0; }

int factorial(int n) {
    if (n < 0) throw std::invalid_argument("Factorial of negative number");
    if (n <= 1) return 1;
    int result = 1;
    for (int i = 2; i < n; ++i) {
        int prev = result;
        result *= i;
        if (result / i != prev)
            throw std::overflow_error("Factorial overflow");
    }
    return result;
}

int fibonacci(int n) {
    if (n < 0) throw std::invalid_argument("Fibonacci of negative number");
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; ++i) { int t = a + b; a = b; b = t; }
    return b;
}

int power(int base, int exponent) {
    if (exponent < 0) throw std::invalid_argument("Negative exponent not supported");
    int result = 1;
    for (int i = 0; i < exponent; ++i) {
        int prev = result;
        result *= base;
        if (base != 0 && result / base != prev)
            throw std::overflow_error("Power overflow");
    }
    return result;
}

} // namespace mathlib