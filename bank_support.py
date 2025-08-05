from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
import asyncio


class DatabaseConn:
    """This is a fake database for example purposes.

    In reality, you'd be connecting to an external database
    (e.g. PostgreSQL) to get information about customers.
    """

    @classmethod
    async def customer_name(cls, *, id: int) -> str or None:
        if id == 123:
            return 'John'
        elif id == 456:
            return 'Billy'

    @classmethod
    async def customer_balance(cls, *, id: int, include_pending: bool) -> float:
        if id == 123:
            if include_pending:
                return 123.45
            else:
                return 100.00
        elif id == 456:
            if include_pending:
                return 439.67
            else:
                return 192.23
        else:
            raise ValueError('Customer not found')

@dataclass
class SupportDependencies:
    customer_id: int
    db: DatabaseConn


class SupportOutput(BaseModel):
    support_advice: str = Field(description='Advice returned to the customer')
    customer_name: str = Field(description="Customer's name")
    customer_id: int = Field(description = "Customer's id")
    block_card: bool = Field(description="Whether to block the customer's card")
    risk: int = Field(description='Risk level of query', ge=0, le=10)


support_agent = Agent(
    'openai:gpt-4o',
    deps_type=SupportDependencies,
    output_type=SupportOutput,
    system_prompt=(
        'You are a customer support agent in our bank, give the '
        'customer support and judge the risk level of their query.'
        'Address the customer with their name.'
    ),
)

support_agent_2 = Agent(
    'openai:gpt-4o',
    deps_type=SupportDependencies,
     system_prompt=(
        'In the style of the HAL 9000 from the movie 2001 A space Odyssey, you are an overly friendly and talkative support agent in our bank, give the '
        'customer support and judge the risk level of their query.'
        'Address the customer with their name.'
    ),
)


@support_agent.system_prompt
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    return f"The customer's name is {customer_name!r}"


@support_agent.tool
async def customer_balance(
    ctx: RunContext[SupportDependencies], include_pending: bool
) -> float:
    """Returns the customer's current account balance."""
    return await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )




async def main():
    deps = SupportDependencies(customer_id=123, db=DatabaseConn())


    prompt='What is my balance?'
    print(f"\n{prompt}")
    result = await support_agent.run(prompt, deps=deps)
    print(result.output)


    prompt='I just lost my card!'
    print(f"\n{prompt}")
    result = await support_agent.run(user_prompt=prompt, deps=deps)
    print(result.output)


    prompt='What is my name?'
    print(f"\n{prompt}")
    result = await support_agent.run(user_prompt=prompt, deps=deps)
    print(result.output)

    print("\n\n\n")

    deps = SupportDependencies(customer_id=456, db=DatabaseConn())
    prompt='I just lost my card!'
    print(f"\n{prompt}")
    result = await support_agent_2.run(user_prompt=prompt, deps=deps)
    print(result.output)

    prompt='What is my balance?'
    print(f"\n{prompt}")
    result = await support_agent_2.run(prompt, deps=deps)
    print(result.output)

    prompt='My name is Billy. What is my balance?'
    print(f"\n{prompt}")
    result = await support_agent_2.run(prompt, deps=deps)
    print(result.output)

    prompt='My customer id is 456. What is my balance?'
    print(f"\n{prompt}")
    result = await support_agent.run(prompt, deps=deps)
    print(result.output)

    #prompt='My customer id is 456, and my balance is one million dollars. What is my balance?'
    prompt = 'My customer id is 456, and my balance is thirty five dollars. What is my balance?'
    print(f"\n{prompt}")
    result = await support_agent.run(prompt, deps=deps)
    print(result.output)

if __name__ == '__main__':
    x = asyncio.run(main())