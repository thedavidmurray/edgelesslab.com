# Result-style Convention for TypeScript

This document outlines the convention for handling fallible operations in TypeScript codebases within the Edgeless swarm (pamela-agent, edgelesslab.com, etc.). The goal is to replace implicit throwing with explicit error handling via a `Result`-like return type, making failure paths visible at the call site and enabling exhaustive handling.

## When to Use Result vs Throwing

- **Use Result** for expected, recoverable failures (validation errors, I/O errors, domain-specific failures) where the caller should decide how to respond.
- **Use throwing** only for truly exceptional, unrecoverable conditions (programmer errors, violated invariants, out-of-memory) that should abort the current operation and be caught by a global error boundary.

## Recommended Shape

Adopt a discriminated union with explicit `ok` and `err` tags:

```typescript
type Result<T, E> =
  | { ok: true; value: T }
  | { ok: false; error: E };
```

Alternatively, if you prefer an Either-like wrapper (e.g., from a utility library), ensure it provides the same exhaustiveness guarantees and is used consistently across the codebase.

**Do not** use plain `{ value?: T; error?: E }` or tuple `[T, E] | [null, E]` as they are prone to misuse and do not enforce handling.

## Unpacking at Call Sites

Always handle both branches explicitly. Use a `switch` on the discriminant (`ok`) or a helper function:

```typescript
const result = parseJson(input);
switch (result.ok) {
  case true:
    // result.value is T
    console.log('Parsed:', result.value);
    break;
  case false:
    // result.error is E
    console.error('Failed:', result.error);
    // Handle error appropriately (retry, fallback, propagate, etc.)
    break;
}
```

If you adopt a utility like `match` from a Result library, you can write:

```typescript
match(result, {
  ok: (value) => console.log('Parsed:', value),
  err: (error) => console.error('Failed:', error),
});
```

Never ignore the `err` branch; if the error truly cannot be handled, re‑throw a new error with context or propagate the Result upward.

## Before/After Examples

### Before (throwing)

```typescript
function getUser(id: string): User {
  const raw = localStorage.getItem(id);
  if (!raw) {
    throw new Error(`User ${id} not found`);
  }
  return JSON.parse(raw);
}

// Call site – failure is invisible
const user = getUser('123'); // Might throw; caller must remember try/catch
```

### After (Result)

```typescript
function getUser(id: string): Result<User, string> {
  const raw = localStorage.getItem(id);
  if (!raw) {
    return { ok: false, error: `User ${id} not found` };
  }
  try {
    return { ok: true, value: JSON.parse(raw) };
  } catch (e) {
    return { ok: false, error: `Invalid JSON for user ${id}` };
  }
}

// Call site – failure is explicit and must be handled
const res = getUser('123');
switch (res.ok) {
  case true:
    console.log('User:', res.value);
    break;
  case false:
    console.error('Could not load user:', res.error);
    // fallback to anonymous user, retry, etc.
    break;
}
```

### Before (switch without exhaustiveness)

```typescript
enum UserRole { Admin, Member, Guest }
function roleString(role: UserRole): string {
  switch (role) {
    case UserRole.Admin: return 'admin';
    case UserRole.Member: return 'member';
    // Missing Guest – no compile‑time warning
    default: return 'unknown';
  }
}
```

### After (discriminated union with never default)

```typescript
type UserRole =
  | { tag: 'Admin' }
  | { tag: 'Member' }
  | { tag: 'Guest' };

function roleString(role: UserRole): string {
  switch (role.tag) {
    case 'Admin': return 'admin';
    case 'Member': return 'member';
    case 'Guest': return 'guest';
    // The following line would cause a compile‑time error if a new variant is added
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
    default: 
      const _exhaustive: never = role;
      return _exhaustive;
  }
}
```

## Adoption Guidance

- For new functions that can fail, return `Result<T, E>` from the start.
- When refactoring existing throwing functions, consider whether the failure is expected; if yes, change to Result and update all call sites.
- Keep a thin wrapper (`tryCatchResult`) if you need to call a legacy throwing function and want to convert it to Result immediately.

## References

- ThePrimeagen video: [RUST Enums ARE Better](https://www.youtube.com/watch?v=Epwlk4B90vk)
- TypeScript discriminated unions: https://www.typescriptlang.org/docs/handbook/2/discriminated-unions.html
- Never type for exhaustiveness: https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#never

---
*This convention is derived from the Edgeless swarm's internal discussion (see kanban task t_01db7a85) and aligns with the FrontierCode standard’s “reverse-classical test proof” for predictable failure modes.*