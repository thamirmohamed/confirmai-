export default function Header() {
  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-8 py-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          Dashboard
        </h1>

        <p className="text-sm text-slate-500">
          Welcome back! Here's what's happening today.
        </p>
      </div>

      <div className="flex items-center gap-4">
        <input
          type="text"
          placeholder="Search..."
          className="w-72 rounded-xl border border-slate-300 px-4 py-2 outline-none focus:border-blue-500"
        />

        <button className="rounded-xl bg-slate-900 px-5 py-2 text-white hover:bg-slate-800">
          Notifications
        </button>
      </div>
    </header>
  );
}