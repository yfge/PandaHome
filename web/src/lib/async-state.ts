export type AsyncState<T> =
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "empty" }
  | { status: "error"; message: string };

export function isLoadingState<T>(state: AsyncState<T>): state is { status: "loading" } {
  return state.status === "loading";
}

export function isErrorState<T>(state: AsyncState<T>): state is { status: "error"; message: string } {
  return state.status === "error";
}

export function isEmptyState<T>(state: AsyncState<T>): state is { status: "empty" } {
  return state.status === "empty";
}

export function isSuccessState<T>(state: AsyncState<T>): state is { status: "success"; data: T } {
  return state.status === "success";
}
