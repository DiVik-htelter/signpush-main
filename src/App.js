import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./pages/layout";
import Home from "./pages/home";
import Documents from "./pages/documents";
import Login from "./pages/login";
import Registration from "./pages/registration";
import RequireAuth from "./components/require-auth";

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route element={<RequireAuth />}> {/* RequireAuth - это защищенный маршрут Все вложенные в него Route будут проверяться на авторизацию  */}
                    <Route path="/" element={<Layout />}>
                        <Route index element={<Home />} /> {/* index это дочерний маршрут, который отображается по умолчанию, когда родительский маршрут активен (path="/") */}
                    </Route>
                    <Route path="/documents" element={<Layout />}>
                        <Route index element={<Documents />} />  {/* страница с загруженными документами в БД */}
                    </Route>
                </Route>

                <Route path="/login" element={<Login />}></Route>
                <Route path="/registration" element={<Registration />}></Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;
