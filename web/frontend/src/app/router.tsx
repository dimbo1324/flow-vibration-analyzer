import { createBrowserRouter } from 'react-router-dom'
import { DashboardPage } from '../pages/DashboardPage'
import { DemoAnalysisPage } from '../pages/DemoAnalysisPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <DashboardPage />,
  },
  {
    path: '/demo',
    element: <DemoAnalysisPage />,
  },
])
