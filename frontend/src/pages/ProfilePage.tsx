import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
} from "react";

import { Link } from "react-router-dom";

import { apiRequest } from "../api";


type User = {
  id: number;
  name: string;
  email: string;
  bio: string | null;
  skills: string | null;
};

type Publication = {
  id: number;
  author_id: number;
  type: "startup" | "vacancy";
  title: string;
  description: string;
  looking_for: string;
  status: "active" | "closed";
  created_at: string;
  updated_at: string;
};

type ApplicationStatus =
  | "pending"
  | "accepted"
  | "rejected";

type Application = {
  id: number;
  publication_id: number;
  applicant_id: number;
  message: string;
  status: ApplicationStatus;
  created_at: string;
  updated_at: string;
};

type IncomingApplication = Application & {
  applicant_name: string;
  matched_skills: string[];
  explanation: string;
};

type Tab =
  | "profile"
  | "publications"
  | "sent"
  | "received";


export function ProfilePage() {
  const [tab, setTab] =
    useState<Tab>("profile");

  const [user, setUser] =
    useState<User | null>(null);

  const [publications, setPublications] =
    useState<Publication[]>([]);

  const [sent, setSent] =
    useState<Application[]>([]);

  const [received, setReceived] =
    useState<IncomingApplication[]>([]);

  const [publicationTitles, setPublicationTitles] =
    useState<Record<number, string>>({});

  const [name, setName] =
    useState("");

  const [bio, setBio] =
    useState("");

  const [skills, setSkills] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  const [
    editingPublication,
    setEditingPublication,
  ] = useState<Publication | null>(null);

  const [editTitle, setEditTitle] =
    useState("");

  const [
    editDescription,
    setEditDescription,
  ] = useState("");

  const [
    editLookingFor,
    setEditLookingFor,
  ] = useState("");

  const [editing, setEditing] =
    useState(false);

  const [deletingPublicationId, setDeletingPublicationId] =
    useState<number | null>(null);


  const loadData =
    useCallback(async () => {
      setLoading(true);
      setError("");

      try {
        const [
          userData,
          publicationData,
          sentData,
          receivedData,
        ] = await Promise.all([
          apiRequest("/users/me"),
          apiRequest(
            "/users/me/publications",
          ),
          apiRequest(
            "/applications/sent",
          ),
          apiRequest(
            "/applications/received",
          ),
        ]);

        setUser(userData);
        setPublications(publicationData);
        setSent(sentData);
        setReceived(receivedData);

        setName(userData.name);
        setBio(userData.bio ?? "");
        setSkills(userData.skills ?? "");

        const ids = Array.from(
          new Set<number>([
            ...sentData.map(
              (item: Application) =>
                item.publication_id,
            ),
            ...receivedData.map(
              (item: Application) =>
                item.publication_id,
            ),
          ]),
        );

        const titleEntries =
          await Promise.all(
            ids.map(async (id) => {
              try {
                const publication =
                  await apiRequest(
                    `/publications/${id}`,
                  );

                return [
                  id,
                  publication.title,
                ] as const;
              } catch {
                return [
                  id,
                  `Публикация #${id}`,
                ] as const;
              }
            }),
          );

        setPublicationTitles(
          Object.fromEntries(titleEntries),
        );
      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Не удалось загрузить кабинет",
        );
      } finally {
        setLoading(false);
      }
    }, []);


  useEffect(() => {
  // Initial profile data loading is intentional.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  loadData();
}, [loadData]);


  async function saveProfile(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const data =
        await apiRequest(
          "/users/me",
          {
            method: "PATCH",
            body: JSON.stringify({
              name,
              bio,
              skills,
            }),
          },
        );

      setUser(data);

      setSuccess(
        "Профиль сохранён",
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Не удалось сохранить профиль",
      );
    } finally {
      setSaving(false);
    }
  }


  async function processApplication(
    applicationId: number,
    action: "accept" | "reject",
  ) {
    setError("");
    setSuccess("");

    try {
      await apiRequest(
        `/applications/${applicationId}/${action}`,
        {
          method: "PATCH",
        },
      );

      setSuccess(
        action === "accept"
          ? "Отклик принят"
          : "Отклик отклонён",
      );

      await loadData();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Не удалось обработать отклик",
      );
    }
  }


  async function changePublicationStatus(
    publicationId: number,
    status: "active" | "closed",
  ) {
    setError("");
    setSuccess("");

    try {
      await apiRequest(
        `/publications/${publicationId}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            status,
          }),
        },
      );

      setSuccess(
        status === "active"
          ? "Публикация снова активна"
          : "Публикация закрыта",
      );

      await loadData();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Не удалось изменить статус публикации",
      );
    }
  }


  function startEditing(
    publication: Publication,
  ) {
    setEditingPublication(publication);

    setEditTitle(
      publication.title,
    );

    setEditDescription(
      publication.description,
    );

    setEditLookingFor(
      publication.looking_for,
    );

    setError("");
    setSuccess("");
  }


  async function savePublication(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!editingPublication) {
      return;
    }

    setEditing(true);
    setError("");
    setSuccess("");

    try {
      await apiRequest(
        `/publications/${editingPublication.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            title: editTitle,
            description:
              editDescription,
            looking_for:
              editLookingFor,
          }),
        },
      );

      setEditingPublication(null);

      setSuccess(
        "Публикация обновлена",
      );

      await loadData();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Не удалось сохранить публикацию",
      );
    } finally {
      setEditing(false);
    }
  }


  async function deletePublication(
    publication: Publication,
  ) {
    const confirmed = window.confirm(
      `Удалить публикацию «${publication.title}» и все связанные отклики? Это действие нельзя отменить.`,
    );

    if (!confirmed) {
      return;
    }

    setDeletingPublicationId(publication.id);
    setError("");
    setSuccess("");

    try {
      await apiRequest(
        `/publications/${publication.id}`,
        { method: "DELETE" },
      );

      setSuccess(
        "Публикация и связанные отклики удалены",
      );

      await loadData();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Не удалось удалить публикацию",
      );
    } finally {
      setDeletingPublicationId(null);
    }
  }


  function getPublicationTitle(
    publicationId: number,
  ) {
    return (
      publicationTitles[
        publicationId
      ] ??
      `Публикация #${publicationId}`
    );
  }


  if (loading) {
    return (
      <main className="min-h-screen bg-slate-50 p-8 text-slate-500">
        Загружаем личный кабинет...
      </main>
    );
  }


  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <Link
            to="/"
            className="text-sm font-semibold text-slate-600 hover:text-slate-900"
          >
            ← Лента
          </Link>

          <div className="font-bold text-slate-900">
            Business Club
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Личный кабинет
          </h1>

          {user && (
            <p className="mt-2 text-slate-500">
              {user.email}
            </p>
          )}
        </div>

        <div className="mt-8 flex gap-2 overflow-x-auto pb-2">
          <TabButton
            active={tab === "profile"}
            onClick={() =>
              setTab("profile")
            }
          >
            Профиль
          </TabButton>

          <TabButton
            active={
              tab === "publications"
            }
            onClick={() =>
              setTab("publications")
            }
          >
            Мои публикации
          </TabButton>

          <TabButton
            active={tab === "sent"}
            onClick={() =>
              setTab("sent")
            }
          >
            Мои отклики
          </TabButton>

          <TabButton
            active={
              tab === "received"
            }
            onClick={() =>
              setTab("received")
            }
          >
            Входящие

            {received.filter(
              (item) =>
                item.status ===
                "pending",
            ).length > 0 && (
              <span className="ml-2 rounded-full bg-red-500 px-2 py-0.5 text-xs text-white">
                {
                  received.filter(
                    (item) =>
                      item.status ===
                      "pending",
                  ).length
                }
              </span>
            )}
          </TabButton>
        </div>

        {error && (
          <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {success && (
          <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-700">
            {success}
          </div>
        )}

        {tab === "profile" && (
          <form
            onSubmit={saveProfile}
            className="mt-6 max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
          >
            <h2 className="text-xl font-bold text-slate-900">
              Профиль участника
            </h2>

            <div className="mt-6">
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Имя
              </label>

              <input
                value={name}
                onChange={(event) =>
                  setName(
                    event.target.value,
                  )
                }
                minLength={2}
                maxLength={100}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500"
                required
              />
            </div>

            <div className="mt-5">
              <label className="mb-2 block text-sm font-medium text-slate-700">
                О себе
              </label>

              <textarea
                value={bio}
                onChange={(event) =>
                  setBio(
                    event.target.value,
                  )
                }
                rows={4}
                maxLength={1000}
                placeholder="Расскажите немного о себе..."
                className="w-full resize-none rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500"
              />
            </div>

            <div className="mt-5">
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Навыки
              </label>

              <input
                value={skills}
                onChange={(event) =>
                  setSkills(
                    event.target.value,
                  )
                }
                maxLength={1000}
                placeholder="Python, FastAPI, Marketing..."
                className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500"
              />
            </div>

            <button
              type="submit"
              disabled={saving}
              className="mt-6 rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving
                ? "Сохраняем..."
                : "Сохранить"}
            </button>
          </form>
        )}

        {tab ===
          "publications" && (
          <div className="mt-6 space-y-4">
            {publications.length ===
              0 && (
              <EmptyState text="У вас пока нет публикаций." />
            )}

            {publications.map(
              (publication) => (
                <article
                  key={publication.id}
                  className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
                >
                  <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <div className="flex flex-wrap gap-2">
                        <TypeBadge
                          type={
                            publication.type
                          }
                        />

                        <span
                          className={
                            publication.status ===
                            "active"
                              ? "rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700"
                              : "rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500"
                          }
                        >
                          {publication.status ===
                          "active"
                            ? "Активна"
                            : "Закрыта"}
                        </span>
                      </div>

                      <h2 className="mt-4 text-xl font-bold text-slate-900">
                        {
                          publication.title
                        }
                      </h2>

                      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                        {
                          publication.description
                        }
                      </p>

                      <div className="mt-3 text-sm text-slate-600">
                        <span className="font-semibold">
                          Ищем:
                        </span>{" "}
                        {
                          publication.looking_for
                        }
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <Link
                        to={`/publications/${publication.id}`}
                        className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        Открыть
                      </Link>

                      <button
                        onClick={() =>
                          startEditing(
                            publication,
                          )
                        }
                        className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        Редактировать
                      </button>

                      {publication.status ===
                      "active" ? (
                        <button
                          onClick={() =>
                            changePublicationStatus(
                              publication.id,
                              "closed",
                            )
                          }
                          className="rounded-xl border border-red-200 px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-50"
                        >
                          Закрыть
                        </button>
                      ) : (
                        <button
                          onClick={() =>
                            changePublicationStatus(
                              publication.id,
                              "active",
                            )
                          }
                          className="rounded-xl border border-emerald-200 px-4 py-2 text-sm font-semibold text-emerald-700 hover:bg-emerald-50"
                        >
                          Открыть снова
                        </button>
                      )}

                      <button
                        onClick={() =>
                          deletePublication(
                            publication,
                          )
                        }
                        disabled={
                          deletingPublicationId ===
                          publication.id
                        }
                        className="rounded-xl bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {deletingPublicationId ===
                        publication.id
                          ? "Удаляем..."
                          : "Удалить"}
                      </button>
                    </div>
                  </div>
                </article>
              ),
            )}
          </div>
        )}

        {tab === "sent" && (
          <div className="mt-6 space-y-4">
            {sent.length === 0 && (
              <EmptyState text="Вы пока ни на что не откликались." />
            )}

            {sent.map(
              (application) => (
                <article
                  key={application.id}
                  className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h2 className="font-bold text-slate-900">
                      {getPublicationTitle(
                        application.publication_id,
                      )}
                    </h2>

                    <StatusBadge
                      status={
                        application.status
                      }
                    />
                  </div>

                  <p className="mt-4 whitespace-pre-line leading-6 text-slate-600">
                    {
                      application.message
                    }
                  </p>

                  <Link
                    to={`/publications/${application.publication_id}`}
                    className="mt-5 inline-block text-sm font-semibold text-indigo-600 hover:text-indigo-800"
                  >
                    Открыть публикацию →
                  </Link>
                </article>
              ),
            )}
          </div>
        )}

        {tab === "received" && (
          <div className="mt-6 space-y-4">
            {received.length ===
              0 && (
              <EmptyState text="На ваши публикации пока никто не откликнулся." />
            )}

            {received.map(
              (application) => (
                <article
                  key={application.id}
                  className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="text-sm text-slate-400">
                        Кандидат: {application.applicant_name}
                      </div>

                      <h2 className="mt-1 text-lg font-bold text-slate-900">
                        {getPublicationTitle(
                          application.publication_id,
                        )}
                      </h2>
                    </div>

                    <StatusBadge
                      status={
                        application.status
                      }
                    />
                  </div>

                  <p className="mt-4 whitespace-pre-line leading-6 text-slate-600">
                    {
                      application.message
                    }
                  </p>

                  <Link
                    to={`/publications/${application.publication_id}`}
                    className="mt-5 inline-block text-sm font-semibold text-indigo-600 hover:text-indigo-800"
                  >
                    Открыть публикацию →
                  </Link>

                  <section className="mt-5 rounded-2xl border border-indigo-100 bg-indigo-50/60 p-4 sm:p-5">
                    <h3 className="text-sm font-bold text-slate-900">
                      Соответствие навыков
                    </h3>
                    {application.matched_skills.length > 0 && (
                      <>
                        <ul className="mt-3 flex flex-wrap gap-2" aria-label="Совпавшие навыки">
                          {application.matched_skills.map((skill) => (
                            <li key={skill} className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-indigo-700 ring-1 ring-indigo-100">
                              {skill}
                            </li>
                          ))}
                        </ul>
                        <h4 className="mt-4 text-sm font-semibold text-slate-800">
                          Почему кандидат подходит
                        </h4>
                      </>
                    )}
                    <p className="mt-2 break-words text-sm leading-6 text-slate-600">
                      {application.explanation}
                    </p>
                    <p className="mt-3 text-xs leading-5 text-slate-500">
                      Подсказка по указанным навыкам, не оценка кандидата. Решение принимаете вы.
                    </p>
                  </section>

                  {application.status ===
                    "pending" && (
                    <div className="mt-5 flex flex-wrap gap-3">
                      <button
                        onClick={() =>
                          processApplication(
                            application.id,
                            "accept",
                          )
                        }
                        className="rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700"
                      >
                        Принять
                      </button>

                      <button
                        onClick={() =>
                          processApplication(
                            application.id,
                            "reject",
                          )
                        }
                        className="rounded-xl border border-red-200 px-5 py-2.5 text-sm font-semibold text-red-600 hover:bg-red-50"
                      >
                        Отклонить
                      </button>
                    </div>
                  )}
                </article>
              ),
            )}
          </div>
        )}
      </section>

      {editingPublication && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/40 sm:items-center sm:p-6">
          <div className="max-h-[95vh] w-full overflow-y-auto rounded-t-3xl bg-white p-6 shadow-xl sm:max-w-xl sm:rounded-3xl sm:p-8">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">
                  Редактировать публикацию
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Изменения сразу появятся
                  в ленте.
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  setEditingPublication(
                    null,
                  )
                }
                className="rounded-full px-3 py-2 text-xl text-slate-400 hover:bg-slate-100"
              >
                ×
              </button>
            </div>

            <form
              onSubmit={
                savePublication
              }
              className="mt-7 space-y-5"
            >
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Название
                </label>

                <input
                  value={editTitle}
                  onChange={(event) =>
                    setEditTitle(
                      event.target.value,
                    )
                  }
                  minLength={3}
                  maxLength={150}
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Описание
                </label>

                <textarea
                  value={
                    editDescription
                  }
                  onChange={(event) =>
                    setEditDescription(
                      event.target.value,
                    )
                  }
                  minLength={10}
                  rows={5}
                  className="w-full resize-none rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Кого ищете?
                </label>

                <input
                  value={
                    editLookingFor
                  }
                  onChange={(event) =>
                    setEditLookingFor(
                      event.target.value,
                    )
                  }
                  minLength={2}
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() =>
                    setEditingPublication(
                      null,
                    )
                  }
                  className="flex-1 rounded-xl border border-slate-300 px-4 py-3 font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Отмена
                </button>

                <button
                  type="submit"
                  disabled={editing}
                  className="flex-1 rounded-xl bg-indigo-600 px-4 py-3 font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {editing
                    ? "Сохраняем..."
                    : "Сохранить"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}


function TabButton({
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


function TypeBadge({
  type,
}: {
  type: "startup" | "vacancy";
}) {
  return (
    <span
      className={
        type === "startup"
          ? "rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700"
          : "rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700"
      }
    >
      {type === "startup"
        ? "Стартап"
        : "Вакансия"}
    </span>
  );
}


function StatusBadge({
  status,
}: {
  status: ApplicationStatus;
}) {
  if (status === "accepted") {
    return (
      <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700">
        ✓ Принят
      </span>
    );
  }

  if (status === "rejected") {
    return (
      <span className="rounded-full bg-red-50 px-3 py-1 text-sm font-semibold text-red-700">
        Отклонён
      </span>
    );
  }

  return (
    <span className="rounded-full bg-amber-50 px-3 py-1 text-sm font-semibold text-amber-700">
      На рассмотрении
    </span>
  );
}


function EmptyState({
  text,
}: {
  text: string;
}) {
  return (
    <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center text-slate-500">
      {text}
    </div>
  );
}
