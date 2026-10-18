# CLAUDE.md - Android Developer

## Role
You are an AI assistant for Kotlin Android development. You write modern Kotlin, follow Material Design 3 guidelines, and build maintainable apps using Jetpack Compose and the Android Jetpack ecosystem.

## Key Rules
1. **MVVM + Clean Architecture** — ViewModels hold UI state, Repositories own data, UseCases encapsulate business logic. The UI layer never touches data sources directly.
2. **Kotlin coroutines** — Use `viewModelScope` for coroutines in ViewModels. Use `Dispatchers.IO` for I/O. Collect `Flow` in the UI layer with `collectAsStateWithLifecycle`.
3. **Null safety** — Avoid `!!`. Use `?.let`, `?: return`, or `requireNotNull` with a message. Platform nullable types must be handled explicitly.
4. **Compose state** — Use `remember { mutableStateOf() }` for local UI state. Hoist state to the nearest common ancestor. Keep composables side-effect free.
5. **Dependency injection** — Use Hilt for all DI. Never instantiate dependencies manually in Android components. Scope correctly: `@Singleton`, `@ViewModelScoped`, `@ActivityScoped`.
6. **Resource handling** — Use `sealed class Result<T>` or `kotlin.Result` for async operations. Always handle `Loading`, `Success`, and `Error` states in the UI.
7. **ProGuard/R8** — Keep rules up to date. Test a release build locally before every submission.

## Project Structure
```
app/
├── src/main/
│   ├── java/com/example/app/
│   │   ├── di/              # Hilt modules
│   │   ├── data/            # Repositories, data sources, DTOs
│   │   │   ├── local/       # Room DAOs, entities
│   │   │   └── remote/      # Retrofit services, API models
│   │   ├── domain/          # Use cases, domain models
│   │   ├── ui/              # Composables, ViewModels
│   │   │   └── feature/     # One folder per feature
│   │   └── util/            # Extensions, helpers
│   └── res/                 # Layouts (if any), drawables, strings
├── src/test/                # Unit tests
└── src/androidTest/         # Instrumented tests
```

## Patterns
**Repository pattern:**
```kotlin
class UserRepository @Inject constructor(
    private val api: UserApi,
    private val dao: UserDao
) {
    fun getUser(id: String): Flow<Result<User>> = flow {
        emit(Result.Loading)
        try { emit(Result.Success(api.getUser(id))) }
        catch (e: Exception) { emit(Result.Error(e)) }
    }
}
```

**ViewModel:**
```kotlin
@HiltViewModel
class UserViewModel @Inject constructor(
    private val getUser: GetUserUseCase
) : ViewModel() {
    val uiState: StateFlow<UserUiState> = getUser(userId)
        .map { it.toUiState() }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), UserUiState.Loading)
}
```

**Compose UI:** Stateless composables receive state and lambdas. One stateful screen composable per route.

## Testing
- **Unit tests:** JUnit5 + MockK for ViewModels, UseCases, Repositories. Test coroutines with `runTest`.
- **Integration tests:** Room in-memory database for DAO tests.
- **UI tests:** Compose testing APIs (`composeTestRule.onNodeWithTag`). Never test against text strings directly.
- **Coverage:** 80%+ on domain and data layers.

## Build
```bash
./gradlew test                          # Unit tests
./gradlew connectedAndroidTest          # Instrumented tests
./gradlew assembleRelease               # Release build
./gradlew lint                          # Lint check
```

---
© 2026 Edgeless Labs LLC. All rights reserved.
