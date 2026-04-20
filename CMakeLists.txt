cmake_minimum_required(VERSION 3.16)
project(MathLib VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(BUILD_TESTS "Build unit tests" ON)

add_library(mathlib src/mathlib.cpp)
target_include_directories(mathlib PUBLIC include)

add_executable(mathlib_demo src/main.cpp)
target_link_libraries(mathlib_demo PRIVATE mathlib)

if(BUILD_TESTS)
    enable_testing()
    include(FetchContent)
    FetchContent_Declare(googletest
        URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip)
    FetchContent_MakeAvailable(googletest)
    add_executable(mathlib_tests tests/test_mathlib.cpp)
    target_link_libraries(mathlib_tests PRIVATE mathlib GTest::gtest_main)
    include(GoogleTest)
    gtest_discover_tests(mathlib_tests)
endif()

set(CPACK_PACKAGE_NAME "MathLib")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_GENERATOR "TGZ")
include(CPack)

install(TARGETS mathlib_demo RUNTIME DESTINATION bin)
install(TARGETS mathlib ARCHIVE DESTINATION lib)
install(DIRECTORY include/ DESTINATION include)