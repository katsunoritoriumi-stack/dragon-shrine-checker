// Vercel Edge Middleware — Basic 認証で非公開化（無料 / Hobby プランで動作）
// 全アセットをエッジで検査するため、認証前は index.html すら配信されない。
// 資格情報は Vercel の環境変数 BASIC_AUTH_USER / BASIC_AUTH_PASS で注入する
// （公開リポジトリのためコードには秘密を書かない）。

export const config = {
  // すべてのパスを保護する
  matcher: "/:path*",
};

export default function middleware(request) {
  const USER = process.env.BASIC_AUTH_USER || "katsu";
  const PASS = process.env.BASIC_AUTH_PASS;

  // パスワード未設定時は「誤って公開しない」ため全面ブロック
  if (!PASS) {
    return new Response("非公開設定中です（BASIC_AUTH_PASS 未設定）", { status: 503 });
  }

  const header = request.headers.get("authorization");
  if (header) {
    const [scheme, encoded] = header.split(" ");
    if (scheme === "Basic" && encoded) {
      const decoded = atob(encoded);
      const i = decoded.indexOf(":");
      const user = decoded.slice(0, i);
      const pass = decoded.slice(i + 1);
      if (user === USER && pass === PASS) {
        return; // 認証成功 → 通常配信
      }
    }
  }

  return new Response("認証が必要です", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="RIAT (private)"' },
  });
}
