import { createBrowserRouter } from 'react-router-dom'
import { Shell } from '../shared/ui/Shell'
import { DashboardPage } from '../pages/DashboardPage'
import { DemoAnalysisPage } from '../pages/DemoAnalysisPage'
import { UploadAnalysisPage } from '../pages/UploadAnalysisPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Shell><DashboardPage /></Shell>,
  },
  {
    path: '/demo',
    element: <Shell><DemoAnalysisPage /></Shell>,
  },
  {
    path: '/upload',
    element: <Shell><UploadAnalysisPage /></Shell>,
  },
])
