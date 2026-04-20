#include "mathlib.h"
#include <iostream>

int main() {
    std::cout << "MathLib v1.0.0 — Compiler Team Product" << std::endl;
    std::cout << "add(5, 3)      = " << mathlib::add(5, 3) << std::endl;
    std::cout << "factorial(10)  = " << mathlib::factorial(10) << std::endl;
    std::cout << "power(2, 10)   = " << mathlib::power(2, 10) << std::endl;
    std::cout << "fibonacci(10)  = " << mathlib::fibonacci(10) << std::endl;
    return 0;
}