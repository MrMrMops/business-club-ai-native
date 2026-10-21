import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
} from "react";

import { apiRequest } from "../api";
import { Link } from "react-router-dom";
import { Recommendations } from "./Recommendations";

type User = {
  id: number;
  name: string;
  email: string;
  bio: string | null;
  skills: string | null;
};

type PublicationType =
  | "startup"
  | "vacancy";

type Publication = {
  id: number;
  author_id: number;
  author_name: string;
  type: PublicationType;
  title: string;
  description: string;
  looking_for: string;
  status: "active" | "closed";
  created_at: string;
  updated_at: string;
};

type Filter =
  | "all"
  | "startup"
  | "vacancy";


export function FeedPage() {
  const [user, setUser] =
    useState<User | null>(null);

  const [publications, setPublications] =
    useState<Publication[]>([]);

  const [filter, setFilter] =
    useState<Filter>("all");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [createOpen, setCreateOpen] =
    useState(false);

  const [creating, setCreating] =
    useState(false);

  const [type, setType] =
    useState<PublicationType>("startup");

  const [title, setTitle] =
    useState("");

  const [description, setDescription] =
    useState("");

  const [lookingFor, setLookingFor] =
    useState("");


  const loadPublications =
    useCallback(async () => {
      setLoading(true);
      setError("");

      try {
        const path =
          filter === "all"
            ? "/publications"
            : `/publications?publication_type=${filter}`;

        const data =
          await apiRequest(path);

        setPublications(data);
      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Не удалось загрузить публикации",
        );
      } finally {
        setLoading(false);
      }
    }, [filter]);


  useEffect(() => {
    apiRequest("/users/me")
      .then(setUser)
      .catch((error) => {
        setError(
          error instanceof Error
            ? error.message
            : "Не удалось загрузить профиль",
        );
      });
  }, []);


  useEffect(() => {
  // Loading publications when the filter changes is intentional.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  loadPublications();
}, [loadPublications]);


  async function createPublication(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setCreating(true);
    setError("");

    try {
      await apiRequest(
        "/publications",
        {
          method: "POST",
          body: JSON.stringify({
            type,
            title,
            description,
            looking_for: lookingFor,
          }),
        },
      );

      setTitle("");
      setDescription("");
      setLookingFor("");
      setType("startup");

      setCreateOpen(false);

      await loadPublications();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Не удалось создать публикацию",
      );
    } finally {
      setCreating(false);
    }
  }


  function logout() {
    localStorage.removeItem(
      "access_token",
    );

    window.location.href = "/login";
  }


  return (
    <main className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <div>
            <div className="font-bold text-slate-900">
              Business Club
            </div>

            <div className="text-xs text-slate-500">
              Startups
            </div>
          </div>

          <div className="flex items-center gap-3">
            {user && (
              <div className="hidden text-right sm:block">
                <div className="text-sm font-medium text-slate-800">
                  {user.name}
                </div>

                <div className="text-xs text-slate-500">
                  {user.email}
                </div>
              </div>
            )}
            <Link
  to="/profile"
  className="rounded-xl border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
>
  Кабинет
</Link>

            <button
              onClick={logout}
              className="rounded-xl border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Выйти
            </button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">
              Найди команду или проект
            </h1>

            <p className="mt-2 max-w-2xl text-slate-500">
              Стартапы и вакансии участников
              Бизнес-клуба.
            </p>
          </div>

          <button
            onClick={() =>
              setCreateOpen(true)
            }
            className="rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white shadow-sm hover:bg-indigo-700"
          >
            + Создать публикацию
          </button>
        </div>

        <Recommendations skills={user?.skills} />

        <div className="mt-8 flex gap-2 overflow-x-auto pb-2">
          <FilterButton
            active={filter === "all"}
            onClick={() =>
              setFilter("all")
            }
          >
            Все
          </FilterButton>

          <FilterButton
            active={filter === "startup"}
            onClick={() =>
              setFilter("startup")
            }
          >
            Стартапы
          </FilterButton>

          <FilterButton
            active={filter === "vacancy"}
            onClick={() =>
              setFilter("vacancy")
            }
          >
            Вакансии
          </FilterButton>
        </div>

        {error && (
          <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-red-700">
            {error}
          </div>
        )}

        {loading && (
          <div className="mt-8 text-slate-500">
            Загружаем публикации...
          </div>
        )}

        {!loading &&
          publications.length === 0 && (
            <div className="mt-8 rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
              <div className="text-lg font-semibold text-slate-800">
                Здесь пока ничего нет
              </div>

              <p className="mt-2 text-slate-500">
                Станьте первым, кто опубликует
                предложение.
              </p>

              <button
                onClick={() =>
                  setCreateOpen(true)
                }
                className="mt-5 rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-700"
              >
                Создать публикацию
              </button>
            </div>
          )}

        <div className="mt-8 grid gap-5 md:grid-cols-2">
          {publications.map(
            (publication) => (
              <article
                key={publication.id}
                className="flex flex-col rounded-3xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className="flex items-start justify-between gap-4">
                  <span
                    className={
                      publication.type ===
                      "startup"
                        ? "rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700"
                        : "rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700"
                    }
                  >
                    {publication.type ===
                    "startup"
                      ? "Стартап"
                      : "Вакансия"}
                  </span>

                  <span className="text-xs text-slate-400">
                    {formatDate(
                      publication.created_at,
                    )}
                  </span>
                </div>

                <h2 className="mt-5 text-xl font-bold text-slate-900">
                  {publication.title}
                </h2>

                <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-600">
                  {publication.description}
                </p>

                <div className="mt-5 rounded-2xl bg-slate-50 p-4">
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Ищем
                  </div>

                  <div className="mt-1 text-sm font-medium text-slate-700">
                    {publication.looking_for}
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4">
                  <span className="text-sm text-slate-500">
                    Автор: {publication.author_name}
                  </span>

                  <Link
  to={`/publications/${publication.id}`}
  className="text-sm font-semibold text-indigo-600 hover:text-indigo-800"
>
  Подробнее →
</Link>
                </div>
              </article>
            ),
          )}
        </div>
      </section>

      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/40 p-0 sm:items-center sm:p-6">
          <div className="max-h-[95vh] w-full overflow-y-auto rounded-t-3xl bg-white p-6 shadow-xl sm:max-w-xl sm:rounded-3xl sm:p-8">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">
                  Новая публикация
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Расскажите о проекте или
                  вакансии.
                </p>
              </div>

              <button
                onClick={() =>
                  setCreateOpen(false)
                }
                className="rounded-full px-3 py-2 text-xl text-slate-400 hover:bg-slate-100"
              >
                ×
              </button>
            </div>

            <form
              onSubmit={createPublication}
              className="mt-7 space-y-5"
            >
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Тип публикации
                </label>

                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() =>
                      setType("startup")
                    }
                    className={
                      type === "startup"
                        ? "rounded-xl border-2 border-indigo-600 bg-indigo-50 px-4 py-3 font-semibold text-indigo-700"
                        : "rounded-xl border border-slate-300 px-4 py-3 font-medium text-slate-600"
                    }
                  >
                    🚀 Стартап
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      setType("vacancy")
                    }
                    className={
                      type === "vacancy"
                        ? "rounded-xl border-2 border-indigo-600 bg-indigo-50 px-4 py-3 font-semibold text-indigo-700"
                        : "rounded-xl border border-slate-300 px-4 py-3 font-medium text-slate-600"
                    }
                  >
                    💼 Вакансия
                  </button>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Название
                </label>

                <input
                  value={title}
                  onChange={(event) =>
                    setTitle(
                      event.target.value,
                    )
                  }
                  minLength={3}
                  maxLength={150}
                  placeholder="Например, AI Case Trainer"
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Описание
                </label>

                <textarea
                  value={description}
                  onChange={(event) =>
                    setDescription(
                      event.target.value,
                    )
                  }
                  minLength={10}
                  rows={5}
                  placeholder="Что вы создаёте и почему это интересно?"
                  className="w-full resize-none rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Кого ищете?
                </label>

                <input
                  value={lookingFor}
                  onChange={(event) =>
                    setLookingFor(
                      event.target.value,
                    )
                  }
                  minLength={2}
                  placeholder="Backend developer, дизайнер..."
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() =>
                    setCreateOpen(false)
                  }
                  className="flex-1 rounded-xl border border-slate-300 px-4 py-3 font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Отмена
                </button>

                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 rounded-xl bg-indigo-600 px-4 py-3 font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {creating
                    ? "Публикуем..."
                    : "Опубликовать"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}


function FilterButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={
        active
          ? "whitespace-nowrap rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
          : "whitespace-nowrap rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
      }
    >
      {children}
    </button>
  );
}


function formatDate(
  dateString: string,
) {
  return new Intl.DateTimeFormat(
    "ru-RU",
    {
      day: "numeric",
      month: "short",
    },
  ).format(new Date(dateString));
}
