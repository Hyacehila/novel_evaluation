export const routes = {
  dashboard: "/",
  history: "/history",
  newTask: "/tasks/new",
  task: (taskId: string) => `/tasks/${taskId}`,
  result: (taskId: string) => `/tasks/${taskId}/result`,
};
