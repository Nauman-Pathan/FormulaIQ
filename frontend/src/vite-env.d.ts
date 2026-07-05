/// <reference types="vite/client" />

declare module 'react-plotly.js' {
  import { Component } from 'react'
  import { PlotlyHTMLElement, Layout, Data, Config } from 'plotly.js'

  export interface PlotParams {
    data: Data[]
    layout: Partial<Layout>
    config?: Partial<Config>
    frames?: any[]
    style?: React.CSSProperties
    className?: string
    onInitialized?: (figure: Readonly<{ data: Data[]; layout: Layout; frames: any[] }>, graphDiv: PlotlyHTMLElement) => void
    onUpdate?: (figure: Readonly<{ data: Data[]; layout: Layout; frames: any[] }>, graphDiv: PlotlyHTMLElement) => void
    onPurge?: (graphDiv: PlotlyHTMLElement) => void
    onError?: (err: Error) => void
    onHover?: (event: Readonly<PlotlyHTMLElement>) => void
    onUnhover?: (event: Readonly<PlotlyHTMLElement>) => void
    onClick?: (event: Readonly<PlotlyHTMLElement>) => void
    onSelected?: (event: Readonly<PlotlyHTMLElement>) => void
    useResizeHandler?: boolean
    debug?: boolean
  }

  export default class Plot extends Component<PlotParams> {}
}
