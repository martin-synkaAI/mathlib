#include "mathlib.h"
#include <gtest/gtest.h>
#include <stdexcept>

TEST(Add, Positive) { EXPECT_EQ(mathlib::add(2, 3), 5); }
TEST(Add, Negative) { EXPECT_EQ(mathlib::add(-2, -3), -5); }
TEST(Add, Overflow) { EXPECT_THROW(mathlib::add(2147483647, 1), std::overflow_error); }
TEST(Subtract, Basic) { EXPECT_EQ(mathlib::subtract(5, 3), 2); }
TEST(Multiply, Basic) { EXPECT_EQ(mathlib::multiply(3, 4), 12); }
TEST(Multiply, Zero) { EXPECT_EQ(mathlib::multiply(0, 999), 0); }
TEST(Divide, Basic) { EXPECT_DOUBLE_EQ(mathlib::divide(10, 3), 10.0/3.0); }
TEST(Divide, ByZero) { EXPECT_THROW(mathlib::divide(1, 0), std::invalid_argument); }
TEST(Factorial, Basic) { EXPECT_EQ(mathlib::factorial(5), 120); }
TEST(Factorial, Zero) { EXPECT_EQ(mathlib::factorial(0), 1); }
TEST(Factorial, Negative) { EXPECT_THROW(mathlib::factorial(-1), std::invalid_argument); }
TEST(Fibonacci, Basic) { EXPECT_EQ(mathlib::fibonacci(10), 55); }
TEST(Power, Basic) { EXPECT_EQ(mathlib::power(2, 10), 1024); }
TEST(Power, NegExp) { EXPECT_THROW(mathlib::power(2, -1), std::invalid_argument); }
TEST(IsEven, True) { EXPECT_TRUE(mathlib::is_even(42)); }
TEST(IsEven, False) { EXPECT_FALSE(mathlib::is_even(7)); }