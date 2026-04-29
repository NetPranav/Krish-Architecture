export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="auth-page">
      <div className="auth-top-bar" />
      <div className="auth-container">
        {children}
      </div>
    </div>
  );
}
