export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-sm border border-warn/30 bg-warn-tint px-4 py-3 text-sm text-warn">
      {message}
    </div>
  );
}
