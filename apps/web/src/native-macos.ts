type NativeWindow = Window & {
  webkit?: { messageHandlers?: { companion?: { postMessage(value: string): void } } };
};

export function nativeShell(): boolean {
  return Boolean((window as NativeWindow).webkit?.messageHandlers?.companion);
}

export function nativeUnlock(): void {
  (window as NativeWindow).webkit?.messageHandlers?.companion?.postMessage("unlock");
}
