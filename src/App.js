import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import Layout from "./pages/layout";
import Upload from "./pages/upload";
import SendDocument from "./pages/send-document";
import Profile from "./pages/profile";
import Settings from "./pages/settings";
import Documents from "./pages/documents";
import SignatureVerification from "./pages/signature-verification";
import Login from "./pages/login";
import Registration from "./pages/registration";
import RequireAuth from "./components/require-auth";
import { SidebarProvider } from "./context/SidebarContext";
import { setNavigate, setCurrentPath } from "./api/axios";

// Компонент для инициализации навигации в axios интерцепторе
function NavigationInitializer({ children }) {
    const navigate = useNavigate();
    const location = useLocation();
    
    useEffect(() => {
        setNavigate(navigate);
    }, [navigate]);
    
    useEffect(() => {
        setCurrentPath(location.pathname);
    }, [location.pathname]);
    
    return children;
}

function App() {
    return (
        <BrowserRouter>
            <NavigationInitializer>
                <SidebarProvider>
                    <Routes>
                    <Route element={<RequireAuth />}>
                        <Route path="/" element={<Layout />}>
                            <Route index element={<Documents />} />
                        </Route>
                        <Route path="/my-documents" element={<Layout />}>
                            <Route index element={<Documents />} />
                        </Route>
                        <Route path="/upload" element={<Layout />}>
                            <Route index element={<Upload />} />
                        </Route>
                        <Route path="/send-document" element={<Layout />}>
                            <Route index element={<SendDocument />} />
                        </Route>
                        <Route path="/profile" element={<Layout />}>
                            <Route index element={<Profile />} />
                        </Route>
                        <Route path="/settings" element={<Layout />}>
                            <Route index element={<Settings />} />
                        </Route>
                        <Route path="/documents" element={<Layout />}>
                            <Route index element={<Documents />} />
                        </Route>
                        <Route path="/signature-verification" element={<Layout />}>
                            <Route index element={<SignatureVerification />} />
                        </Route>
                    </Route>

                    <Route path="/login" element={<Login />}></Route>
                    <Route path="/registration" element={<Registration />}></Route>
                </Routes>
                </SidebarProvider>
            </NavigationInitializer>
        </BrowserRouter>
    );
}

export default App;
