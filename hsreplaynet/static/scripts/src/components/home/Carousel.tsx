import React from "react";

interface Props {
	from: React.ReactNode;
	to: React.ReactNode;
	onHoverStart?: () => void;
	onHoverEnd?: () => void;
}

interface State {
	shift: boolean;
	index: number;
}

export default class Carousel extends React.Component<Props, State> {
	private timeout: number | null = null;

	constructor(props: Props, context?: any) {
		super(props, context);
		this.state = {
			shift: true,
			index: 0,
		};
	}

	public componentDidUpdate(
		prevProps: Readonly<Props>,
		prevState: Readonly<State>,
		prevContext: any,
	): void {
		if (prevState.shift === this.state.shift) {
			this.setState(
				state => ({
					shift: false,
					index: state.index + 1,
				}),
				() => {
					if (this.timeout !== null) {
						window.clearTimeout(this.timeout);
					}
					this.timeout = window.setTimeout(() => {
						this.setState({ shift: true });
						this.timeout = null;
					}, 50);
				},
			);
		}
	}

	public componentWillUnmount(): void {
		if (this.timeout !== null) {
			window.clearTimeout(this.timeout);
		}
	}

	public render(): React.ReactNode {
		return (
			<div
				className="carousel"
				onMouseOver={this.onMouseOver}
				onMouseOut={this.onMouseOut}
			>
				<div
					className="carousel-window"
					style={{ left: this.state.shift ? "-100%" : "0%" }}
					key={this.state.index}
				>
					<div className="carousel-panel">{this.props.from}</div>
					<div className="carousel-panel">{this.props.to}</div>
				</div>
			</div>
		);
	}

	private onMouseOver = () =>
		this.props.onHoverStart && this.props.onHoverStart();
	private onMouseOut = () => this.props.onHoverEnd && this.props.onHoverEnd();
}
