// vite.config.js
import { defineConfig } from "file:///C:/Users/reddy/OneDrive/Desktop/sih-transport/frontend/node_modules/vite/dist/node/index.js";
import react from "file:///C:/Users/reddy/OneDrive/Desktop/sih-transport/frontend/node_modules/@vitejs/plugin-react/dist/index.js";
var vite_config_default = defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      // Proxy API calls to backend — avoids CORS issues in dev
      "/api": {
        target: process.env.VITE_API_BASE_URL || "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path
      },
      "/ws": {
        target: process.env.VITE_WS_URL || "ws://localhost:8000",
        ws: true,
        changeOrigin: true
      },
      "/health": {
        target: process.env.VITE_API_BASE_URL || "http://localhost:8000",
        changeOrigin: true
      }
    }
  },
  resolve: {
    alias: {
      "@": "/src"
    }
  },
  define: {
    // Expose environment variables to the app
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version)
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxyZWRkeVxcXFxPbmVEcml2ZVxcXFxEZXNrdG9wXFxcXHNpaC10cmFuc3BvcnRcXFxcZnJvbnRlbmRcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIkM6XFxcXFVzZXJzXFxcXHJlZGR5XFxcXE9uZURyaXZlXFxcXERlc2t0b3BcXFxcc2loLXRyYW5zcG9ydFxcXFxmcm9udGVuZFxcXFx2aXRlLmNvbmZpZy5qc1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vQzovVXNlcnMvcmVkZHkvT25lRHJpdmUvRGVza3RvcC9zaWgtdHJhbnNwb3J0L2Zyb250ZW5kL3ZpdGUuY29uZmlnLmpzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSdcbmltcG9ydCByZWFjdCBmcm9tICdAdml0ZWpzL3BsdWdpbi1yZWFjdCdcblxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcbiAgcGx1Z2luczogW3JlYWN0KCldLFxuICBzZXJ2ZXI6IHtcbiAgICBob3N0OiAnMC4wLjAuMCcsXG4gICAgcG9ydDogNTE3MyxcbiAgICBwcm94eToge1xuICAgICAgLy8gUHJveHkgQVBJIGNhbGxzIHRvIGJhY2tlbmQgXHUyMDE0IGF2b2lkcyBDT1JTIGlzc3VlcyBpbiBkZXZcbiAgICAgICcvYXBpJzoge1xuICAgICAgICB0YXJnZXQ6IHByb2Nlc3MuZW52LlZJVEVfQVBJX0JBU0VfVVJMIHx8ICdodHRwOi8vbG9jYWxob3N0OjgwMDAnLFxuICAgICAgICBjaGFuZ2VPcmlnaW46IHRydWUsXG4gICAgICAgIHJld3JpdGU6IChwYXRoKSA9PiBwYXRoLFxuICAgICAgfSxcbiAgICAgICcvd3MnOiB7XG4gICAgICAgIHRhcmdldDogcHJvY2Vzcy5lbnYuVklURV9XU19VUkwgfHwgJ3dzOi8vbG9jYWxob3N0OjgwMDAnLFxuICAgICAgICB3czogdHJ1ZSxcbiAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlLFxuICAgICAgfSxcbiAgICAgICcvaGVhbHRoJzoge1xuICAgICAgICB0YXJnZXQ6IHByb2Nlc3MuZW52LlZJVEVfQVBJX0JBU0VfVVJMIHx8ICdodHRwOi8vbG9jYWxob3N0OjgwMDAnLFxuICAgICAgICBjaGFuZ2VPcmlnaW46IHRydWUsXG4gICAgICB9LFxuICAgIH0sXG4gIH0sXG4gIHJlc29sdmU6IHtcbiAgICBhbGlhczoge1xuICAgICAgJ0AnOiAnL3NyYycsXG4gICAgfSxcbiAgfSxcbiAgZGVmaW5lOiB7XG4gICAgLy8gRXhwb3NlIGVudmlyb25tZW50IHZhcmlhYmxlcyB0byB0aGUgYXBwXG4gICAgX19BUFBfVkVSU0lPTl9fOiBKU09OLnN0cmluZ2lmeShwcm9jZXNzLmVudi5ucG1fcGFja2FnZV92ZXJzaW9uKSxcbiAgfSxcbn0pXG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQWtXLFNBQVMsb0JBQW9CO0FBQy9YLE9BQU8sV0FBVztBQUVsQixJQUFPLHNCQUFRLGFBQWE7QUFBQSxFQUMxQixTQUFTLENBQUMsTUFBTSxDQUFDO0FBQUEsRUFDakIsUUFBUTtBQUFBLElBQ04sTUFBTTtBQUFBLElBQ04sTUFBTTtBQUFBLElBQ04sT0FBTztBQUFBO0FBQUEsTUFFTCxRQUFRO0FBQUEsUUFDTixRQUFRLFFBQVEsSUFBSSxxQkFBcUI7QUFBQSxRQUN6QyxjQUFjO0FBQUEsUUFDZCxTQUFTLENBQUMsU0FBUztBQUFBLE1BQ3JCO0FBQUEsTUFDQSxPQUFPO0FBQUEsUUFDTCxRQUFRLFFBQVEsSUFBSSxlQUFlO0FBQUEsUUFDbkMsSUFBSTtBQUFBLFFBQ0osY0FBYztBQUFBLE1BQ2hCO0FBQUEsTUFDQSxXQUFXO0FBQUEsUUFDVCxRQUFRLFFBQVEsSUFBSSxxQkFBcUI7QUFBQSxRQUN6QyxjQUFjO0FBQUEsTUFDaEI7QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUFBLEVBQ0EsU0FBUztBQUFBLElBQ1AsT0FBTztBQUFBLE1BQ0wsS0FBSztBQUFBLElBQ1A7QUFBQSxFQUNGO0FBQUEsRUFDQSxRQUFRO0FBQUE7QUFBQSxJQUVOLGlCQUFpQixLQUFLLFVBQVUsUUFBUSxJQUFJLG1CQUFtQjtBQUFBLEVBQ2pFO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
