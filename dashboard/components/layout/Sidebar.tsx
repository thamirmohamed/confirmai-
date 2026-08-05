export default function Sidebar() {
  const menu = [
    "Dashboard",
    "Orders",
    "Customers",
    "Analytics",
    "Integrations",
    "Billing",
    "Settings",
  ];

  return (
    <aside className="w-64 min-h-screen bg-slate-950 text-white p-6">
      <h1 className="text-2xl font-bold mb-10">
        ConfirmAI
      </h1>

      <nav className="space-y-2">
        {menu.map((item) => (
          <button
            key={item}
            className="w-full rounded-lg px-4 py-3 text-left transition hover:bg-slate-800"
          >
            {item}
          </button>
        ))}
      </nav>
    </aside>
  );
}