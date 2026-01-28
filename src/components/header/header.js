import {Navbar} from "react-bootstrap";
import './header.css';
import {useCookies} from "react-cookie";
import {useNavigate} from "react-router-dom";
import {useContext} from "react";
import AuthContext from "../../context/AuthProvider";
import { Link } from "react-router-dom";

function Header() {
    const {setAuth} = useContext(AuthContext)
    const [cookies, removeCookie] = useCookies(['user']);

    const navigate = useNavigate();

    const handleLogout = async (e) => {
        e.preventDefault();

        removeCookie('user');
        setAuth(null);

        navigate('/', { replace: true });
    };

    return (
        <Navbar className="navbar navbar-light justify-content-between">
            <img alt="logo" src="logo.png" className="navbar-brand logo"></img>
            <div className="collapse navbar-collapse" id="navbarNavDropdown">
                <ul className="navbar-nav">
                    <li className="nav-item">
                        <Link className="nav-link" to="/">Создать документ </Link>
                    </li>
                    <li className="nav-item">
                        <Link className="nav-link" to="/documents">Документы</Link>
                    </li>
                </ul>
            </div>
            <div className="form-inline login">
                {cookies?.user} <button className="button btn btn-primary" onClick={handleLogout}>Выход</button>
            </div>
        </Navbar>
    );
}

export default Header;