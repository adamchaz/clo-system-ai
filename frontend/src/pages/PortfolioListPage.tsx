import React from 'react';
import { useNavigate } from 'react-router-dom';
import PortfolioList from '../components/portfolio/PortfolioList';
import { Portfolio } from '../store/api/cloApi';

const PortfolioListPage: React.FC = () => {
  const navigate = useNavigate();

  const handlePortfolioView = (portfolio: Portfolio) => {
    // Navigate to portfolio details page
    navigate(`/portfolios/details/${portfolio.id}`);
  };

  const handlePortfolioEdit = (portfolio: Portfolio) => {
    // Navigate to portfolio edit page (if it exists)
    console.log('Edit portfolio:', portfolio.id);
    // navigate(`/portfolios/edit/${portfolio.id}`);
  };

  const handlePortfolioCreate = () => {
    // Navigate to portfolio creation page (if it exists)
    console.log('Create new portfolio');
    // navigate('/portfolios/create');
  };

  return (
    <PortfolioList
      onPortfolioView={handlePortfolioView}
      onPortfolioEdit={handlePortfolioEdit}
      onPortfolioCreate={handlePortfolioCreate}
    />
  );
};

export default PortfolioListPage;