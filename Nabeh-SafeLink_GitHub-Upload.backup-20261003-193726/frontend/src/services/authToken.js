// Deliberately memory-only: access tokens are not persisted in browser storage.
let accessToken = null;

export const getAccessToken = () => accessToken;
export const setAccessToken = (token) => {
  accessToken = typeof token === 'string' && token.trim() ? token : null;
};
export const clearAccessToken = () => {
  accessToken = null;
};
