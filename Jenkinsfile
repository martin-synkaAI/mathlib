// ============================================================================
// Jenkinsfile for MathLib — "Compiler Team" product
// ============================================================================
// THIS IS THE WHOLE FILE. Three lines of actual content.
//
// @Library loads the shared library from the 'iar-shared-lib' repo.
// The underscore (_) imports all global variables from vars/.
// Then we call cppPipeline() which runs the full standardized pipeline.
//
// GitHub Actions equivalent:
//   jobs:
//     build:
//       uses: org/platform/.github/workflows/cpp-service.yml@main
//       with:
//         image: mathlib
//         version: '1.0.0'
//
// The product team doesn't need to know Jenkins pipeline syntax.
// They just set their product name and version. YOU own the pipeline.
// ============================================================================

@Library('shared-lib') _

cppPipeline(
    image: 'mathlib',
    version: '1.0.0'
)