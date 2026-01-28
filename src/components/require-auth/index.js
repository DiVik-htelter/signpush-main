import useAuth from "../../hooks/useAuth";
import {Navigate, Outlet, useLocation} from "react-router-dom";
import {useCookies} from "react-cookie";

const RequireAuth = () => {
    const { location } = useLocation();
    const [cookies] = useCookies(['user']);

    return ((cookies?.user && cookies.user !== 'undefined') ? <Outlet/> : <Navigate to="/login" state={{from: location}} replace />);
}

export default RequireAuth;