import ReactPaginate from 'react-paginate';

function Paginator({ items, itemsPerPage, handlePageClick}) {
  const pageCount = Math.ceil(items.length / itemsPerPage);

  return (
    <>
      {pageCount !== 1 && <ReactPaginate
        previousLabel="Предыдущая"
        nextLabel="Следующая"
        pageClassName="page-item"
        pageLinkClassName="page-link"
        previousClassName="page-item"
        previousLinkClassName="page-link"
        nextClassName="page-item"
        nextLinkClassName="page-link"
        breakLabel="..."
        breakClassName="page-item"
        breakLinkClassName="page-link"
        pageCount={pageCount}
        containerClassName="pagination"
        activeClassName="active"
        onPageChange={handlePageClick}
        marginPagesDisplayed={1}
        pageRangeDisplayed={1}
        renderOnZeroPageCount={null}
      />}
    </>
  );
}

export default Paginator;