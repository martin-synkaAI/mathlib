# ===== Stage 1: BUILDER =====
FROM gcc:12 AS builder
RUN apt-get update && \
    apt-get install -y --no-install-recommends cmake ninja-build cppcheck && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY CMakeLists.txt .
COPY include/ include/
COPY src/ src/
COPY tests/ tests/
RUN cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=ON \
    && cmake --build build --parallel $(nproc)
RUN cd build && ctest --output-on-failure --output-junit test-results.xml
RUN cppcheck --enable=all --xml --xml-version=2 \
    --suppress=missingIncludeSystem -I include/ src/ 2> build/cppcheck-report.xml || true
RUN cd build && cpack

# ===== Stage 2: RUNTIME =====
FROM debian:bookworm-slim AS runtime
RUN useradd -m appuser
COPY --from=builder /app/build/mathlib_demo /usr/local/bin/
USER appuser
ENTRYPOINT ["mathlib_demo"]

# ===== Stage 3: TEST RESULTS =====
FROM scratch AS test-results
COPY --from=builder /app/build/test-results.xml /
COPY --from=builder /app/build/cppcheck-report.xml /