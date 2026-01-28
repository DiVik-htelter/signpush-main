import Header from "../../components/header/header";
import {Outlet} from "react-router-dom";

function Layout() {
  return (
    <div className="App">
      <Header></Header>
        <div className="container">
            <Outlet />
        </div>
    </div>
  );
}

export default Layout;
