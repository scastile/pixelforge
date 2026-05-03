import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-[var(--background)]">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-[var(--background)]/80 border-b border-[var(--card-border)]">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[var(--accent)] flex items-center justify-center">
              <span className="text-white font-bold text-lg">P</span>
            </div>
            <h1 className="text-2xl font-semibold text-[var(--foreground)]">PixelForge</h1>
          </div>
          <nav className="flex items-center gap-4">
            <button className="btn btn-secondary text-sm py-2 px-4">
              Sign In
            </button>
            <button className="btn btn-primary text-sm py-2 px-4">
              Get Started
            </button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 py-20 text-center">
        <h2 className="text-6xl font-bold text-[var(--foreground)] mb-6 tracking-tight">
          Image editing,<br />
          <span style={{ color: 'var(--accent)' }}>reimagined.</span>
        </h2>
        <p className="text-xl text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Privacy-first image manipulation with 44 professional tools across 8 categories. 
          Your images never leave your server.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link href="/editor" className="btn btn-primary text-base py-3 px-8">
            Start Editing
          </Link>
          <button className="btn btn-secondary text-base py-3 px-8">
            View on GitHub
          </button>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-6 py-16 border-t border-[var(--card-border)]">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 rounded-2xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h4 className="text-lg font-semibold text-[var(--foreground)] mb-2">Privacy First</h4>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              Your images never leave your server. Complete control over your data.
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 rounded-2xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h4 className="text-lg font-semibold text-[var(--foreground)] mb-2">AI-Powered</h4>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              Choose from multiple AI models for optimal results on any hardware.
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 rounded-2xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </div>
            <h4 className="text-lg font-semibold text-[var(--foreground)] mb-2">Self-Hosted</h4>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              Deploy anywhere with Docker. No subscriptions, no limits.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--card-border)] py-8 mt-16">
        <div className="max-w-7xl mx-auto px-6 text-center text-sm text-zinc-600 dark:text-zinc-400">
          <p>PixelForge — Built with ❤️ for the self-hosted community</p>
          <p className="mt-2">MIT License • Open Source • Privacy First</p>
        </div>
      </footer>
    </div>
  );
}
