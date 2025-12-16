import "./globals.css";

export const metadata = {
  title: "Nexus AI Daily (MVP)",
  description: "Daily AI intelligence dashboard (PRD edition semantics)"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
