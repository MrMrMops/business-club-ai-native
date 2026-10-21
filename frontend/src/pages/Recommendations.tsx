import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest } from "../api";

type Recommendation = {
  id: number;
  title: string;
  type: "startup" | "vacancy";
  author_name: string;
  description: string;
  matched_skills: string[];
  explanation: string;
};

export function Recommendations({ skills }: { skills: string | null | undefined }) {
  const [items, setItems] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    apiRequest("/publications/recommended")
      .then((data: Recommendation[]) => {
        if (active) setItems(data);
      })
      .catch(() => {
        if (active) setFailed(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [skills, attempt]);

  function retry() {
    setFailed(false);
    setLoading(true);
    setAttempt((value) => value + 1);
  }

  return (
    <section aria-labelledby="recommendations-heading" className="mt-8 rounded-3xl border border-indigo-100 bg-gradient-to-br from-indigo-50 via-white to-violet-50 p-5 sm:p-7">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="recommendations-heading" className="text-xl font-bold tracking-tight text-slate-900">✨ Рекомендуем вам</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">Проекты, которым могут пригодиться ваши навыки.</p>
        </div>
        <Link to="/profile" className="text-sm font-semibold text-indigo-700 hover:underline">Мои навыки →</Link>
      </div>

      {loading ? (
        <p role="status" className="mt-5 text-sm text-slate-500">Подбираем подходящие проекты…</p>
      ) : failed ? (
        <div role="status" className="mt-5 text-sm text-slate-600">
          Рекомендации временно недоступны. Обычная лента доступна ниже.
          <button type="button" onClick={retry} className="ml-2 font-semibold text-indigo-700 hover:underline">Попробовать снова</button>
        </div>
      ) : skills !== undefined && !skills?.trim() ? (
        <div className="mt-5 rounded-2xl bg-white/80 p-5 text-sm leading-6 text-slate-600">
          Добавьте навыки в профиль — подберём стартапы и вакансии, которым они нужны.
          <Link to="/profile" className="mt-3 block font-semibold text-indigo-700 hover:underline">Заполнить навыки →</Link>
        </div>
      ) : items.length === 0 ? (
        <p className="mt-5 text-sm leading-6 text-slate-600">Пока нет совпадений с вашими навыками. Загляните в общую ленту или уточните навыки в профиле — например, Python, UX/UI или продуктовая аналитика.</p>
      ) : (
        <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <article key={item.id} className="flex min-w-0 flex-col rounded-2xl border border-indigo-100 bg-white p-5 shadow-sm">
              <span className="self-start rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">{item.type === "startup" ? "Стартап" : "Вакансия"}</span>
              <h3 className="mt-4 break-words text-lg font-bold text-slate-900">{item.title}</h3>
              <p className="mt-1 break-words text-xs text-slate-500">Автор: {item.author_name}</p>
              <p className="mt-3 line-clamp-3 break-words text-sm leading-6 text-slate-600">{item.description}</p>
              <div className="mt-4 flex flex-wrap gap-2" aria-label="Совпавшие навыки">
                {item.matched_skills.map((skill) => <span key={skill} className="rounded-lg bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-800">{skill}</span>)}
              </div>
              <div className="mt-4 rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-600">
                <p className="font-semibold text-slate-800">Почему вам подходит</p>
                <p className="mt-1">{item.explanation}</p>
              </div>
              <Link to={`/publications/${item.id}`} className="mt-auto pt-5 text-sm font-semibold text-indigo-700 hover:underline">Посмотреть проект →</Link>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
