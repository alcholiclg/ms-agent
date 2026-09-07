# GitHub 镜像基础环境验证

仅验证 GitHub 托管 runner 的资源、公共依赖下载、Docker 构建，以及 Python 3.12 / Node 22 / pnpm 10.17.1 / uv 0.12.8 的基本运行。

工作流只在个人 fork 的 `feat/github-image-preflight` 分支相关文件 push 时执行，不使用 secrets，不推送镜像，不上传 PyPI。

ACR 探测只验证匿名网络连通性；401 是预期认证挑战，不代表已验证登录、推送权限或镜像仓库访问。

测试镜像不包含 MS-Agent 应用。完整的 WebUI、wheel、SSR、CSS 和 SSE 验收需在迁移与打包改造完成后单独运行。
