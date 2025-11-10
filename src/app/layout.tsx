import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/ui/toaster";
import { LayoutWithSidebar } from "@/components/LayoutWithSidebar";
import { ErrorBoundary } from "@/components/ErrorBoundary";

export const metadata: Metadata = {
  title: "Zemixity",
  description: "AI-powered search engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ErrorBoundary>
          <Providers>
            <LayoutWithSidebar>
              {children}
            </LayoutWithSidebar>
            <Toaster />
          </Providers>
        </ErrorBoundary>
      </body>
    </html>
  );
}
