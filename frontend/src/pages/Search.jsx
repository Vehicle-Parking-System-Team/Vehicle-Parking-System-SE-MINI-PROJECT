import { VehicleSearchView } from '../components/VehicleSearchView'

export function SearchPage({ onNavigateToProfile, onNavigateToRegister }) {
  return (
    <div className="search-page" id="search-page-container">
      <VehicleSearchView
        onNavigateToProfile={onNavigateToProfile}
        onNavigateToRegister={onNavigateToRegister}
      />
    </div>
  )
}

export default SearchPage
