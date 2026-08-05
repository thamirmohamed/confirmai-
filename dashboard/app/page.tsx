import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export default function Home() {
  return (
    <main className="flex min-h-screen bg-slate-100">
      <Sidebar />

      <div className="flex flex-1 flex-col">
        <Header />

        <section className="p-8">
          <h2 className="text-3xl font-bold text-slate-900">
            Good Morning, Mohamed 👋
          </h2>

          <p className="mt-2 text-slate-500">
            Here's your business overview for today.
          </p>

          <div className="mt-8 grid grid-cols-4 gap-6">
            <div className="rounded-2xl bg-white p-6 shadow-sm">
              <p className="text-sm text-slate-500">Orders Today</p>
              <h3 className="mt-2 text-3xl font-bold">186</h3>
            </div>

            <div className="rounded-2xl bg-white p-6 shadow-sm">
              <p className="text-sm text-slate-500">Confirmed</p>
              <h3 className="mt-2 text-3xl font-bold text-green-600">164</h3>
            </div>

            <div className="rounded-2xl bg-white p-6 shadow-sm">
              <p className="text-sm text-slate-500">Revenue Protected</p>
              <h3 className="mt-2 text-3xl font-bold">42,580 MAD</h3>
            </div>

            <div className="rounded-2xl bg-white p-6 shadow-sm">
              <p className="text-sm text-slate-500">Needs Review</p>
              <h3 className="mt-2 text-3xl font-bold text-orange-500">4</h3>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}