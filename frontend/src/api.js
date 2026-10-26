import axios from "axios";
const api=axios.create({baseURL:import.meta.env.VITE_API_URL||"http://127.0.0.1:8000",timeout:15000});
api.interceptors.request.use(c=>{const t=localStorage.getItem("taskflow_token");if(t)c.headers.Authorization=`Bearer ${t}`;return c;});
export function errorText(e){const d=e?.response?.data?.detail;if(Array.isArray(d))return d.map(x=>x.msg).join(", ");if(d)return d;if(e?.code==="ERR_NETWORK")return"Cannot reach FastAPI. Check that the backend is running and the API URL is correct.";return e?.message||"Something went wrong";}
export async function login(email,password){const body=new URLSearchParams({username:email,password});const{data}=await api.post("/auth/login",body,{headers:{"Content-Type":"application/x-www-form-urlencoded"}});localStorage.setItem("taskflow_token",data.access_token);return data}
export async function register(username,email,password){return(await api.post("/auth/register",{username,email,password})).data}
export async function getTasks(){const{data}=await api.get("/tasks/");return Array.isArray(data)?data:(data.items||[])}
export async function addTask(payload){return(await api.post("/tasks/",payload)).data}
export async function editTask(id,payload){return(await api.patch(`/tasks/${id}`,payload)).data}
export async function removeTask(id){return api.delete(`/tasks/${id}`)}
